import os
import json
import logging
from google import genai
from PIL import Image
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger(__name__)

# Load Environment Variables
load_dotenv()

# Initialize Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
client = None

if api_key:
    try:
        client = genai.Client(api_key=api_key)
        logger.info("Gemini API Client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API Client: {e}")
else:
    logger.warning("GEMINI_API_KEY not found in environment. OCR features will run in fallback mode.")

def analyze_screenshot(image: Image.Image) -> dict:
    """
    Menganalisis screenshot menggunakan Gemini Vision API.
    Mengekstrak teks, klasifikasi awal, dan entitas penipuan.
    """
    if not client:
        logger.error("Gemini API Client not initialized. Cannot perform OCR.")
        return {
            "text": "Error: Gemini API Client tidak terinisialisasi. Periksa GEMINI_API_KEY.",
            "kategori": "VALID",
            "alasan": "Gemini API Client tidak tersedia.",
            "entitas_penipu": {
                "nomor_hp": "",
                "rekening": "",
                "links": [],
                "bank": "",
                "nama_pemilik": ""
            }
        }

    prompt = """
    Kamu adalah AI pendeteksi Hoaks dan Penipuan untuk masyarakat Indonesia.
    Tugasmu:
    1. Lakukan OCR: Baca dan transkripsikan seluruh teks yang ada di dalam gambar screenshot ini.
    2. Klasifikasikan informasi/percakapan ini menjadi salah satu dari 4 kategori: [VALID, HOAX, PENIPUAN, NETRAL].
       - Jika screenshot ini menunjukkan bukti transfer palsu, chat penipuan pinjol, modus loker bodong, penipuan file APK, giveaway palsu, olshop fiktif, jastip tiket konser palsu, atau chat dari nomor tidak dikenal yang meminta uang/transfer, tandai sebagai PENIPUAN.
       - Jika teks berisi berita bohong tanpa motif penipuan uang secara langsung, tandai sebagai HOAX.
       - Jika teks berisi berita valid atau informasi resmi, tandai sebagai VALID.
       - Jika teks berisi promosi toko resmi, percakapan normal sehari-hari, opini netral, atau pengumuman biasa, tandai sebagai NETRAL.
    3. Ekstrak entitas penipu jika terdeteksi (khususnya untuk kategori PENIPUAN):
       - nomor_hp: Nomor WhatsApp/HP pelaku yang mengirim pesan atau tertera dalam obrolan.
       - rekening: Nomor rekening bank atau e-wallet tujuan transfer pelaku.
       - bank: Nama bank tujuan transfer (misal: BCA, Mandiri, BRI, BNI, GoPay, OVO, Dana).
       - nama_pemilik: Nama pemilik rekening/e-wallet tujuan transfer.
       - links: Daftar link shortener atau URL mencurigakan yang dibagikan pelaku (misal bit.ly, wa.me, t.me, dll.).

    Berikan jawabanmu dalam format JSON murni tanpa markdown formatting (tidak perlu menggunakan ```json ... ```) seperti ini:
    {
      "text": "isi teks lengkap hasil transkripsi OCR...",
      "kategori": "PENIPUAN / HOAX / VALID / NETRAL",
      "alasan": "alasan singkat kenapa diklasifikasikan ke kategori tersebut...",
      "entitas_penipu": {
        "nomor_hp": "nomor HP pelaku jika ada",
        "rekening": "nomor rekening tujuan jika ada",
        "bank": "nama bank tujuan jika ada",
        "nama_pemilik": "nama pemilik rekening jika ada",
        "links": ["daftar link jika ada"]
      }
    }
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, image]
        )
        
        # Bersihkan response text dari markdown syntax jika ada
        resp_text = response.text.strip()
        if resp_text.startswith("```"):
            # Hilangkan pembungkus ```json dan ```
            lines = resp_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            resp_text = "\n".join(lines).strip()

        # Parse JSON
        result = json.loads(resp_text)
        return result
    except Exception as e:
        logger.error(f"Error during Gemini screenshot analysis: {e}")
        return {
            "text": f"Gagal memproses gambar: {str(e)}",
            "kategori": "VALID",
            "alasan": f"Terjadi kesalahan saat memproses gambar dengan Gemini API: {str(e)}",
            "entitas_penipu": {
                "nomor_hp": "",
                "rekening": "",
                "links": [],
                "bank": "",
                "nama_pemilik": ""
            }
        }
