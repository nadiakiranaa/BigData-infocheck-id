from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'analyzed-news',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    consumer_timeout_ms=3000
)

msgs = list(consumer)
print(f"Found {len(msgs)} messages in analyzed-news")
if msgs:
    print(msgs[-1].value.decode('utf-8'))
