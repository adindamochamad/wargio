# Setup MongoDB Atlas & MCP (Hari 1)

## 1. Atlas Cluster

1. Buat cluster **M0** di [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Database user + network access (IP allowlist atau `0.0.0.0/0` untuk dev).
3. Salin connection string ke `.env`:

```env
MONGODB_URI=mongodb+srv://...
MONGODB_DATABASE=wargio_demo
```

## 2. Index & Seed (script)

```bash
pip install -r backend/requirements.txt
python scripts/buat_indeks.py
python scripts/seed_data.py
python scripts/verifikasi_hari1.py
```

## 3. Vector Search Index (manual di Atlas UI)

Search index name: `products_vector_index`  
Collection: `products`

```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "name": [
        { "type": "string" },
        { "type": "vector", "dimensions": 768, "similarity": "cosine" }
      ],
      "name_aliases": [{ "type": "string" }],
      "category": [{ "type": "string" }]
    }
  }
}
```

Embedding diisi saat pipeline fuzzy match (Hari 3). Hari 1 cukup index dibuat.

## 4. MongoDB MCP Server

Install (Node.js):

```bash
npx -y mongodb-mcp-server@latest --help
```

Atau ikuti: [MongoDB MCP Server docs](https://www.mongodb.com/docs/mcp-server/).

### Verifikasi MCP (DoD Hari 1)

Jalankan MCP dengan connection string Atlas, lalu tool **find** pada collection `products`:

```json
{
  "database": "wargio_demo",
  "collection": "products",
  "filter": {
    "$expr": { "$lte": ["$stock_current", "$stock_minimum"] }
  },
  "limit": 10
}
```

Harus return produk dengan stok di bawah minimum (setelah seed).

> Script `verifikasi_hari1.py` menjalankan query yang sama via PyMongo — setara bukti data; MCP tetap wajib diverifikasi manual untuk hackathon.

## 5. Jalankan API

```bash
cd backend
uvicorn app.main:aplikasi --reload --port 8000
curl http://localhost:8000/api/health
```
