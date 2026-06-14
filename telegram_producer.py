import asyncio
import logging
from datetime import datetime, timezone
from telethon import TelegramClient, events
from kafka_helper import send_to_kafka, close_producer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_ID   = 32528523
API_HASH = 'e3b0a95df9afe285392a5371c455f141'
SESSION  = 'infocheckid_session'

TARGET_CHANNELS = [
    'TurnBackHoax',
    'cekfakta',
    'kompascom',
    'detiknews',
    'CNBCIndonesia',
    'tempodotco',
]


async def fetch_historical(client, limit=100):
    logger.info(f"Fetching {limit} historical messages per channel...")
    for channel in TARGET_CHANNELS:
        try:
            chat = await client.get_entity(channel)
            channel_name = getattr(chat, 'title', channel)
            count = 0
            async for message in client.iter_messages(chat, limit=limit):
                message_text = message.message or ''
                if not message_text.strip():
                    continue
                payload = {
                    "channel_name": channel_name,
                    "sender_id": str(message.sender_id or 'unknown'),
                    "message": message_text,
                    "sent_at": message.date.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "ingested_at": datetime.utcnow().isoformat() + "Z"
                }
                send_to_kafka('telegram-messages', payload)
                count += 1
            logger.info(f"[{channel_name}] Historical fetch selesai: {count} pesan")
        except Exception as e:
            logger.error(f"Gagal fetch historical dari '{channel}': {e}")


async def main():
    # Client dibuat di dalam async context — fix untuk Python 3.10+
    client = TelegramClient(SESSION, API_ID, API_HASH)

    @client.on(events.NewMessage(chats=TARGET_CHANNELS))
    async def handle_new_message(event):
        try:
            message = event.message
            message_text = message.message or ''
            if not message_text.strip():
                return
            chat = await event.get_chat()
            channel_name = getattr(chat, 'title', str(chat.id))
            payload = {
                "channel_name": channel_name,
                "sender_id": str(message.sender_id or 'unknown'),
                "message": message_text,
                "sent_at": message.date.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z'),
                "ingested_at": datetime.utcnow().isoformat() + "Z"
            }
            success = send_to_kafka('telegram-messages', payload)
            if success:
                preview = message_text[:80].replace('\n', ' ')
                logger.info(f"[{channel_name}] ✓ Terkirim ke Kafka: '{preview}...'")
            else:
                logger.warning(f"[{channel_name}] ✗ Gagal kirim ke Kafka")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    logger.info("Memulai Telegram scraper InfoCheck ID...")
    await client.start()
    await fetch_historical(client, limit=100)
    logger.info(f"Real-time listener aktif — memantau {len(TARGET_CHANNELS)} channel...")
    await client.run_until_disconnected()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown signal diterima. Menghentikan Telegram scraper...")
        close_producer()