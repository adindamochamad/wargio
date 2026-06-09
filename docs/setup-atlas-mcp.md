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

## 3. Vector Search Index (768d)

Nama index: `products_vector_index` pada collection `products`, field vector: `name_embedding`.

```bash
python scripts/buat_vector_index.py
# Jika cluster M0 penuh (indeks proyek lain):
python scripts/buat_vector_index.py --bebaskan-slot-sample
```

Definisi JSON untuk Atlas CLI: `scripts/products_vector_index.json`.

> **M0:** Satu slot FTS per cluster. Opsi `--bebaskan-slot-sample` hanya menghapus indeks bawaan `sample_mflix.movies/default`, bukan data Wargio.

Embedding `name_embedding` diisi via `python scripts/isi_embedding_produk.py` (butuh `GEMINI_API_KEY`, model `gemini-embedding-001`). Hari 1 cukup index status **READY**.

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
