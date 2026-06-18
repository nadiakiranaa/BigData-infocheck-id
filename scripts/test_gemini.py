import os
from google import genai
from PIL import Image
from dotenv import load_dotenv

# Load API Key dari file .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY belum di-set di file .env")
    exit(1)

# Inisialisasi client baru
client = genai.Client(api_key=api_key)

def analyze_screenshot(image_path: str):
    """Membaca gambar screenshot dan mengklasifikasikan ke Valid/Hoax/Penipuan"""
    try:
        # Buka gambar
        img = Image.open(image_path)
        
        prompt = """
        Kamu adalah AI pendeteksi Hoaks dan Penipuan untuk masyarakat Indonesia.
        PERHATIAN KHUSUS: Gambar ini dilaporkan oleh pengguna sebagai BUKTI PENIPUAN. 
        Meskipun gambarnya terlihat seperti transaksi normal (misal struk transfer sukses atau ucapan terima kasih biasa), 
        kamu harus sangat curiga. Cari kejanggalan sekecil apapun (misal nomor rekening asing, transaksi yang tidak wajar, 
        atau tidak ada barang bukti pengiriman barang). 
        
        Tugasmu:
        1. Baca teks yang ada di dalam gambar screenshot ini.
        2. Klasifikasikan informasi ini menjadi salah satu dari 3 kategori: [VALID, HOAX, PENIPUAN].
           *Jika gambar ini dilaporkan korban sebagai bukti transfer penipuan, berikan klasifikasi PENIPUAN meskipun struknya terlihat asli.*
        3. Jika ini adalah PENIPUAN, tolong ekstrak nomor rekening, nama bank, atau nomor HP pelaku yang tertera di teks.
        
        Berikan jawabanmu dalam format JSON murni seperti ini:
        {
          "kategori": "...",
          "alasan": "...",
          "entitas_penipu": {
            "nomor_hp": "...",
            "rekening": "..."
          }
        }
        """
        
        print(f"Menganalisis {os.path.basename(image_path)} menggunakan Gemini API...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img]
        )
        
        print("\n--- HASIL ANALISIS ---")
        print(response.text)
        
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    import glob
    
    screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshot")
    images = glob.glob(os.path.join(screenshot_dir, "*.png")) + glob.glob(os.path.join(screenshot_dir, "*.jpg"))
    
    if not images:
        print(f"Tidak ada gambar ditemukan di {screenshot_dir}")
    else:
        print(f"Ditemukan {len(images)} gambar. Mengetes 2 gambar pertama...")
        for img_path in images[:2]:
            analyze_screenshot(img_path)
            print("-" * 50)
