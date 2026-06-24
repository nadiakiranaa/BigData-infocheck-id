# InfoCheckID Dashboard API Bridge

REST API FastAPI ringan untuk menjembatani database/Elasticsearch dengan Frontend Dashboard. Saat ini semua controller memakai dummy data in-memory agar endpoint langsung bisa dites di Postman.

## Struktur

```text
api_bridge/
├── main.py                 # FastAPI app, CORS, router registration
├── controllers/            # Business logic dan dummy response
├── data/                   # Dummy in-memory store
├── routers/                # HTTP endpoint definitions
├── schemas/                # Pydantic request/response models
└── services/               # Service simulasi OCR/classification
```

## Menjalankan

Pastikan dependency terpasang:

```bash
pip install -r requirements.txt
```

Start server:

```bash
uvicorn api_bridge.main:app --reload --port 8001
```

Swagger docs:

```text
http://127.0.0.1:8001/docs
```

## Endpoint

```text
GET    /api/stats
GET    /api/live-feed?limit=25
GET    /api/scam-db
POST   /api/scam-db
PUT    /api/scam-db/{record_id}
DELETE /api/scam-db/{record_id}
POST   /api/test-ocr
GET    /health
```

## Contoh Payload Scam DB

```json
{
  "identifier_type": "phone_number",
  "identifier_value": "+6281299900011",
  "owner_name": "Admin Bantuan Prioritas",
  "source": "Telegram user report",
  "report_count": 7,
  "status": "active",
  "notes": "Nomor dipakai untuk meminta OTP dan biaya admin."
}
```

## Contoh Test OCR

Gunakan Postman:

```text
POST /api/test-ocr
Body: form-data
Key: file
Type: File
Value: screenshot.png
```
