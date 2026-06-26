"""
telegram_bot.py
Bot Telegram user-facing untuk InfoCheck ID (Jobdesk Anggota 4).

Alur:
  1. User kirim teks berita / link / screenshot ke bot.
  2. Kalau link -> ambil isi artikelnya dulu (lihat api_client.fetch_article_text).
  3. Kirim ke predict_api.py (Anggota 3) lewat /predict atau /predict-image.
  4. Format hasil (skor + label + alasan) dan balas ke user.

Cara jalanin:
  1. Pastikan predict_api.py sudah running (default di http://localhost:8000).
  2. Buat bot baru via @BotFather di Telegram, copy token-nya.
  3. Set environment variable TELEGRAM_BOT_TOKEN, atau isi langsung di bawah.
  4. Install dependency tambahan:
       pip install python-telegram-bot==21.0.1 beautifulsoup4
  5. Jalankan: python bot/telegram_bot.py
"""

import logging
import os
import sys
import asyncio

if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

# Inisialisasi event loop secara eksplisit HARUS dilakukan setelah set policy
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from api_client import predict_text, predict_image, is_url, fetch_article_text
from formatter import format_text_result, format_image_result

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8779133343:AAH2Em8a7e2yeMeZ6uZ-RZ5QphxWSXUiurA")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Saya InfoCheck ID Bot.\n\n"
        "Kirim ke saya:\n"
        "  - Teks berita yang ingin dicek, atau\n"
        "  - Link artikel berita, atau\n"
        "  - Screenshot chat/postingan yang mencurigakan\n\n"
        "Saya akan cek apakah itu Valid, Hoaks, Penipuan, atau Netral, "
        "lengkap dengan skor dan alasannya."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if not user_text:
        return

    if is_url(user_text):
        processing_msg = await update.message.reply_text(
            "Link terdeteksi, mengambil isi artikel..."
        )
        article_text = fetch_article_text(user_text)
        if not article_text:
            await processing_msg.edit_text(
                "Gagal mengambil isi artikel dari link ini.\n"
                "Coba paste teks beritanya langsung ke chat."
            )
            return
        await processing_msg.edit_text("Artikel berhasil diambil, sedang menganalisis...")
        text_to_check = article_text
    else:
        processing_msg = await update.message.reply_text("Sedang menganalisis, tunggu sebentar...")
        text_to_check = user_text

    result = predict_text(text_to_check)
    reply = format_text_result(result)
    await processing_msg.edit_text(reply)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    processing_msg = await update.message.reply_text(
        "Membaca screenshot (OCR), tunggu sebentar..."
    )

    photo_file = await update.message.photo[-1].get_file()
    image_bytes = bytes(await photo_file.download_as_bytearray())

    result = predict_image(image_bytes)
    reply = format_image_result(result)
    await processing_msg.edit_text(reply)


def main():
    if BOT_TOKEN == "8779133343:AAH2Em8a7e2yeMeZ6uZ-RZ5QphxWSXUiurA":
        logger.warning(
            "TELEGRAM_BOT_TOKEN belum diset! "
            "Set environment variable atau ganti default di kode ini."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("Bot InfoCheck ID berjalan (polling mode)...")
    app.run_polling()


if __name__ == "__main__":
    main()
