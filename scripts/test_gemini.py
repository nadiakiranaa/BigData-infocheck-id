import os
import json
import re
import time
import glob
from google import genai
from PIL import Image
from dotenv import load_dotenv

# Load API Key dari file .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY belum di-set di file .env")
    exit(1)

# Inisialisasi client
client = genai.Client(api_key=api_key)

# Path output JSON untuk prepare_dataset.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_JSON = os.path.join(BASE_DIR, "dataset", "ocr_results.json")


def extract_json_from_response(text: str) -> dict:
    """Parse JSON dari response Gemini (bersihkan markdown code block jika ada)."""
    # Hapus ```json ... ``` jika ada
    text = re.sub(r'```(?:json)?\s*', '', text).strip().rstrip('`').strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Coba cari pola JSON di dalam teks
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {}


def analyze_screenshot(image_path: str) -> dict:
    """
    Membaca gambar screenshot dan mengklasifikasikan ke Valid/Hoax/Penipuan/Netral.
    Mengembalikan dict hasil analisis (untuk disimpan ke JSON).
    """
    try:
        img = Image.open(image_path)

        prompt = """
        Kamu adalah AI pendeteksi Hoaks dan Penipuan untuk masyarakat Indonesia.
        PERHATIAN KHUSUS: Gambar ini dilaporkan oleh pengguna sebagai BUKTI PENIPUAN. 
        Meskipun gambarnya terlihat seperti transaksi normal (misal struk transfer sukses atau ucapan terima kasih biasa), 
        kamu harus sangat curiga. Cari kejanggalan sekecil apapun (misal nomor rekening asing, transaksi yang tidak wajar, 
        atau tidak ada barang bukti pengiriman barang). 
        
        Tugasmu:
        1. Baca dan ekstrak SEMUA teks yang ada di dalam gambar screenshot ini.
        2. Klasifikasikan informasi ini menjadi salah satu dari 4 kategori: [VALID, HOAX, PENIPUAN, NETRAL].
           *Jika gambar ini dilaporkan korban sebagai bukti transfer penipuan, berikan klasifikasi PENIPUAN meskipun struknya terlihat asli.*
           *Jika gambar ini hanya promosi toko resmi atau percakapan biasa, klasifikasikan sebagai NETRAL.*
        3. Jika ini adalah PENIPUAN, tolong ekstrak nomor rekening, nama bank, atau nomor HP pelaku yang tertera di teks.
        
        Berikan jawabanmu dalam format JSON murni (tanpa markdown) seperti ini:
        {
          "kategori": "PENIPUAN",
          "alasan": "...",
          "text": "teks lengkap yang berhasil dibaca dari gambar",
          "entitas_penipu": {
            "nomor_hp": "...",
            "rekening": "..."
          }
        }
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img]
        )

        result = extract_json_from_response(response.text)
        result["filename"] = os.path.basename(image_path)

        # Pastikan field 'text' ada (fallback ke response mentah jika parsing gagal)
        if not result.get("text"):
            result["text"] = response.text[:500]  # fallback

        return result

    except Exception as e:
        print(f"  [ERROR] Gagal memproses {os.path.basename(image_path)}: {e}")
        return {
            "filename": os.path.basename(image_path),
            "kategori": "ERROR",
            "alasan": str(e),
            "text": ""
        }


def run_ocr_all_screenshots(screenshot_dir: str, output_json: str, delay_sec: float = 2.0):
    """
    Proses SEMUA screenshot di folder, simpan hasil ke JSON.
    delay_sec: jeda antar request agar tidak kena rate limit Gemini API.
    """
    images = (
        glob.glob(os.path.join(screenshot_dir, "*.png")) +
        glob.glob(os.path.join(screenshot_dir, "*.jpg")) +
        glob.glob(os.path.join(screenshot_dir, "*.jpeg"))
    )

    if not images:
        print(f"Tidak ada gambar ditemukan di: {screenshot_dir}")
        return

    print(f"Ditemukan {len(images)} gambar di folder Screenshot/")
    print(f"Output akan disimpan ke: {output_json}\n")

    # Load hasil yang sudah ada (untuk resume jika terhenti)
    existing_results = []
    processed_filenames = set()
    if os.path.exists(output_json):
        with open(output_json, "r", encoding="utf-8") as f:
            existing_results = json.load(f)
        processed_filenames = {r.get("filename") for r in existing_results}
        print(f"[RESUME] {len(processed_filenames)} gambar sudah diproses sebelumnya, melanjutkan...\n")

    all_results = existing_results.copy()
    success_count = 0
    skip_count = 0

    for i, img_path in enumerate(images, 1):
        fname = os.path.basename(img_path)

        # Skip jika sudah diproses
        if fname in processed_filenames:
            print(f"  [{i}/{len(images)}] SKIP (sudah ada): {fname}")
            skip_count += 1
            continue

        print(f"  [{i}/{len(images)}] Memproses: {fname}...")
        result = analyze_screenshot(img_path)

        if result.get("kategori") != "ERROR":
            print(f"           → Kategori: {result.get('kategori')} | {result.get('alasan', '')[:60]}")
            success_count += 1
        
        all_results.append(result)

        # Simpan setiap iterasi (agar aman jika terhenti di tengah)
        os.makedirs(os.path.dirname(output_json), exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        # Jeda antar request
        if i < len(images):
            time.sleep(delay_sec)

    # Summary
    print(f"\n{'='*50}")
    print(f"SELESAI! Ringkasan:")
    print(f"  Total gambar     : {len(images)}")
    print(f"  Berhasil diproses: {success_count}")
    print(f"  Di-skip (resume) : {skip_count}")
    penipuan_count = sum(1 for r in all_results if r.get("kategori", "").upper() == "PENIPUAN")
    print(f"  Label PENIPUAN   : {penipuan_count}")
    print(f"\nHasil disimpan ke: {output_json}")
    print(f"Selanjutnya jalankan: python scripts/prepare_dataset.py")
    print(f"untuk memasukkan data OCR ke dalam dataset training.")


if __name__ == "__main__":
    screenshot_dir = os.path.join(BASE_DIR, "Screenshot")

    print("=" * 60)
    print("InfoCheck ID — OCR Screenshot ke Dataset (Anggota 2)")
    print("=" * 60)
    print(f"Memproses semua {len(glob.glob(os.path.join(screenshot_dir, '*.png')))} screenshot...")
    print("(Jeda 2 detik antar gambar agar tidak kena rate limit Gemini)\n")

    run_ocr_all_screenshots(
        screenshot_dir=screenshot_dir,
        output_json=OUTPUT_JSON,
        delay_sec=2.0
    )
