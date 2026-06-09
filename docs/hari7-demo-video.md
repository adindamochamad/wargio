# Hari 7 — Script & Workflow Demo Video Wargio

> **Target:** 2:45–2:55 menit (aman di bawah batas **3:00** — video >3 menit = DQ)  
> **Resolusi:** 1080p · **Subtitle:** Bahasa Inggris wajib · **Upload:** YouTube (unlisted/public)  
> **Tools:** Gamma (slide) · ElevenLabs (VO) · Screen record · CapCut Free

**Live app:** `https://wargio.adindamochamad.com`  
**Atlas:** MongoDB Atlas → database `wargio_demo` (collections: `products`, `transactions`, `customers`)

---

## Checklist sebelum rekam

```bash
export WARGIO_PRODUCTION_URL=https://wargio.adindamochamad.com
bash scripts/smoke_production.sh
bash scripts/rehearsal_demo_video.sh   # latihan query persis seperti di video
```

- [ ] Incognito: buka live URL, chat respons < 5 detik
- [ ] Tab Atlas sudah login (cluster → Browse Collections → `wargio_demo`)
- [ ] Browser zoom 100%, dark mode ON, **EN** toggle ON (semua ketikan chat dalam English)
- [ ] Notifikasi OS mati, Do Not Disturb
- [ ] Mic test ElevenLabs / rekaman ruangan senyap
- [ ] Sesi chat baru: buka incognito atau clear `localStorage` key `wargio-session-id`

---

## English chat cheat sheet (semua scene)

| Scene | Ketik persis di chat (EN toggle ON) |
|-------|-------------------------------------|
| 2 — Stock | `how much indomie goreng stock is left?` |
| 3 — Sale draft | `sold 2 indomie goreng and 1 air mineral aqua 600ml` *(pakai **air mineral**, bukan hanya "mineral aqua")* |
| 3 — Confirm | `yes` |
| 4 — Debt list | `who still owes money this week?` |
| 4 — Payment draft | `Bu Sari paid debt 50000` |
| 4 — Confirm | `yes` |
| 5 — Revenue | `what is this week's revenue?` |
| 5 — Forecast *(opsional)* | `will it be busy tomorrow?` |

Latihan otomatis (curl, header `X-Wargio-Language: en`):

```bash
export WARGIO_PRODUCTION_URL=https://wargio.adindamochamad.com
export WARGIO_DEMO_LANG=en
bash scripts/rehearsal_demo_video.sh
```

---

## Storyboard (shot list)

| # | Waktu | Layer | Isi layar | Audio |
|---|-------|-------|-----------|-------|
| 1 | 0:00–0:18 | Gamma slide | Hook — warung Indonesia | VO EN |
| 2 | 0:18–0:48 | Screen | Stock check + Atlas split | VO EN |
| 3 | 0:48–1:18 | Screen | Record sale (konfirmasi) | VO EN |
| 4 | 1:18–1:48 | Screen | Debt list + payment | VO EN |
| 5 | 1:48–2:18 | Screen | Sales insight + dashboard | VO EN |
| 6 | 2:18–2:42 | Gamma slide | Architecture diagram | VO EN |
| 7 | 2:42–2:55 | Gamma slide | Closing + logo Wargio | VO EN |

**Total VO:** ~2:50 (sisakan 5–10 detik buffer edit CapCut)

---

## A. Prompt Gamma (3 deck / 3 slide utama)

Salin prompt berikut ke [gamma.app](https://gamma.app) — satu prompt per generate. Gaya konsisten: **dark background, hijau `#16a34a`, font Inter, minimal teks, hackathon pitch deck**.

### Prompt 1 — Opening Hook (slide 1, ~15 detik di video)

```
Buat 1 slide presentasi 16:9 untuk hackathon pitch video.

Judul besar: "Wargio"
Subjudul: "AI agent for Indonesia's 64 million micro-retailers"

Visual: foto hero warung/kiosk Indonesia (stock photo style), overlay gelap.
Bullet singkat (max 3):
- 64M micro-retailers manage stock & debt manually
- Handwritten notebooks, memory, no real-time data
- Wargio = natural language assistant in Bahasa Indonesia

Warna aksen hijau #16a34a, background navy gelap, font Inter, clean modern.
Tidak ada paragraf panjang. Logo placeholder bulat hijau dengan huruf W.
```

### Prompt 2 — Architecture (slide 2, scene 2:18–2:42)

```
Buat 1 slide diagram arsitektur 16:9, gaya technical pitch hackathon.

Judul: "How Wargio Works"

Diagram alir horizontal (panah kiri ke kanan):
User (Bahasa Indonesia) → Next.js Frontend → FastAPI (Cloud/VPS)
→ Google Gemini + Agent Builder → MongoDB MCP Server → MongoDB Atlas

Label di bawah stack:
- Read/Write: find, aggregate, insertOne, updateOne
- Vector Search 768d for fuzzy product names
- Live Atlas data (not mock)

Warna: hijau #16a34a untuk node aktif, abu untuk supporting.
Tambahkan badge kecil: "Google Cloud Rapid Agent Hackathon 2026"
Minimal, readable di video 1080p. No tiny text.
```

### Prompt 3 — Closing (slide 3, ~12 detik)

```
Buat 1 slide closing 16:9 hackathon.

Center:
"Wargio"
"AI agent for Indonesia's 64 million micro-retailers"

Footer:
wargio.adindamochamad.com
github.com/adindamochamad/wargio

CTA kecil: "Built with MongoDB Atlas, Gemini, and MCP"

Background gradient hijau gelap ke hitam, Inter font, sangat clean.
```

**Export dari Gamma:** PNG 1920×1080 per slide, atau rekam tab Gamma fullscreen 5 detik/slide.

---

## B. Script ElevenLabs (voice over)

**Pengaturan disarankan**

| Setting | Nilai |
|---------|-------|
| Bahasa | English (US) |
| Voice | *Adam* / *Antoni* / *Josh* — jelas, semi-formal pitch |
| Stability | 55–65% |
| Clarity + Similarity | 75%+ |
| Speed | 0.95–1.0× (jangan >1.05 — nanti susah sync) |

Export per scene (7 file MP3) agar mudah geser di CapCut, **atau** satu file panjang dengan jeda 2 detik antar scene.

---

### VO Scene 1 — Hook (0:00–0:18)

```
Sixty-four million micro-retailers in Indonesia still run their shops with notebooks and memory.

Meet Wargio — an AI business assistant that speaks Bahasa Indonesia and works on live MongoDB Atlas data.
```

**Subtitle EN (CapCut):** sama persis dengan VO.

---

### VO Scene 2 — Stock check (0:18–0:48)

```
Let's check stock in plain language.

The owner asks how much instant noodles are left. Wargio queries Atlas in real time, compares stock to the minimum, and warns when it's time to restock.

On the right, you can see the same product document in MongoDB Atlas — this is live data, not a mock.
```

**On-screen actions (type exactly — English):**

1. Open `https://wargio.adindamochamad.com` (incognito)
2. Click **EN** in the header (language toggle)
3. Type: `how much indomie goreng stock is left?`
4. Wait for reply (stock count + minimum status)
5. **Split screen:** chat on the left, MongoDB Atlas on the right → `wargio_demo` → `products` → filter/search `Indomie Goreng` → show `stock_current`, `stock_minimum`

---

### VO Scene 3 — Record sale (0:48–1:18)

```
Recording a sale is a multi-step agent flow.

The owner describes what sold — in one sentence. Wargio parses items, checks stock, and asks for confirmation before writing.

After confirm, it inserts a transaction and updates stock in Atlas.
```

**On-screen actions (type exactly — English):**

1. Type: `sold 2 indomie goreng and 1 air mineral aqua 600ml`
2. Read the confirmation summary in chat
3. Type: `yes`
4. Wait for success reply + Rupiah total
5. *(Optional)* Atlas → `transactions` → sort `created_at` desc → latest document with `type: sale`
6. *(Optional)* `products` → Indomie / Aqua `stock_current` decreased

> Keep quantities small. Rehearse first — if stock is low, reduce counts in the sentence.

---

### VO Scene 4 — Debt (1:18–1:48)

```
Debt tracking is built in.

Ask who still owes money this week — Wargio lists customers sorted by amount.

Then record a payment: confirm once, and the debt balance updates in Atlas.
```

**On-screen actions (type exactly — English):**

1. Type: `who still owes money this week?`
2. Wait for customer list + amounts
3. Type: `Bu Sari paid debt 50000`
4. Type: `yes` after confirmation
5. *(Optional)* Atlas → `customers` → Bu Sari → `debt_total` decreased

---

### VO Scene 5 — Business insight (1:48–2:18)

```
For business insight, Wargio aggregates sales from hundreds of real transactions.

Ask for weekly revenue — or open the mini dashboard for critical stock and top debt at a glance.
```

**On-screen actions (type exactly — English):**

1. Type: `what is this week's revenue?`
2. Scroll to the **dashboard** above chat (critical stock, total debt, today's sales)
3. *(Quick alternative)* Type: `will it be busy tomorrow?` → day-of-week forecast

> Honest note: "top selling product" intent is not built; use **sales_report** + dashboard — judges still see Atlas aggregation.

---

### VO Scene 6 — Architecture (2:18–2:42)

```
Under the hood: Next.js talks to FastAPI on Google Cloud infrastructure.

Gemini and Agent Builder power classification and reasoning. MongoDB MCP tools — find, aggregate, insert, and update — connect to Atlas with vector search for fuzzy product matching.

Every number you saw came from the database live.
```

**On-screen:** fullscreen Gamma Architecture slide (Prompt 2). Slowly zoom toward the MCP → Atlas arrow.

---

### VO Scene 7 — Closing (2:42–2:55)

```
Wargio — AI agent for Indonesia's sixty-four million micro-retailers.

Try it live, explore the code on GitHub, and built for the Google Cloud Rapid Agent Hackathon twenty twenty-six.
```

**On-screen:** Closing slide (Prompt 3) + URL `wargio.adindamochamad.com` clearly visible.

---

## C. Screen recording

### Tool (pilih satu)

| Tool | Gratis | Catatan |
|------|--------|---------|
| **OBS Studio** | Ya | 1080p60, scene browser+window, paling stabil |
| **ShareX** (Win) | Ya | Region capture |
| **macOS Screenshot** | Ya | Cmd+Shift+5 → Record window |
| **Chrome built-in** | Terbatas | DevTools → tidak disarankan untuk demo |

### OBS setup cepat

1. Canvas **1920×1080**
2. Source: **Window Capture** → tab Chrome (chat Wargio)
3. Scene 2: tambah **Window Capture** Atlas (split 50/50) — atau rekam full screen lalu crop di CapCut
4. Output: MP4, bitrate 8000–12000 kbps
5. Rekam **tanpa** VO dulu (hanya typing + mouse) — audio diganti ElevenLabs di CapCut

### Tips rekaman

- Type **naturally** in English (EN toggle on) — do not paste (visible on video)
- Tunggu balasan penuh sebelum scene berikutnya
- Jika loading >3 detik, **potong** di CapCut atau re-take scene itu saja
- Rekam Atlas **setelah** chat sukses (stok/transaksi sudah berubah) — bukti write live
- Satu take per scene → 5 file pendek lebih mudah edit daripada 1 take panjang

---

## D. CapCut Free — workflow edit

### Import

1. New project → **9:16 jangan dipilih** → pilih **16:9 / 1920×1080**
2. Import: 7 MP3 ElevenLabs + semua clip screen + 3 PNG Gamma

### Urutan timeline

```
[V1] Video/slide
[V2] (opsional) zoom highlight pada chat input
[A1] Voice over ElevenLabs
[A2] (mute) hapus audio mic rekaman asli
[T1] Subtitle English — auto caption dari A1, koreksi manual
```

### Langkah per langkah

1. **Rough cut** — susun scene 1→7, potong jeda kosong
2. **Sync VO** — geser clip video agar ketikan muncul saat VO bilang "asks" / "confirm"
3. **Subtitle EN:** Text → Auto captions → bahasa **English** → edit istilah:
   - Wargio, MongoDB Atlas, MCP, Gemini, FastAPI, Bahasa Indonesia
4. **Transisi:** dissolve 0.3s antar scene (jangan berlebihan)
5. **Musik:** opsional royalty-free sangat pelan (-20dB) — **jangan** menutupi VO
6. **Durasi final:** cek **≤ 2:58** di timeline
7. **Export:** 1080p, 30fps, H.264, bitrate recommended

### Subtitle template (jika manual)

| Waktu | English subtitle |
|-------|------------------|
| 0:00 | 64 million micro-retailers in Indonesia... |
| 0:18 | Stock check in natural language |
| 0:48 | Multi-step sale with confirmation |
| 1:18 | Debt collection and payment |
| 1:48 | Sales aggregation from Atlas |
| 2:18 | Gemini + MCP + MongoDB Atlas |
| 2:42 | Wargio — try it live |

---

## E. Upload YouTube & Devpost

**Judul YouTube:**
```
Wargio — AI Agent for Indonesian Warung | MongoDB + Gemini Hackathon 2026
```

**Deskripsi:**
```
Wargio is an AI business assistant for Indonesia's micro-retailers.
Live demo on MongoDB Atlas with MCP-style tools, Gemini, and FastAPI.

🔗 Live app: https://wargio.adindamochamad.com
🔗 Source: https://github.com/adindamochamad/wargio

Google Cloud Rapid Agent Hackathon 2026 — MongoDB Track
```

- Visibility: **Unlisted** (cukup untuk judge) atau Public
- Verifikasi: buka link di incognito tanpa login
- Isi `docs/devpost-submission.md` field **Demo video**

**Thumbnail:** frame chat + dashboard, teks "Wargio" + "MongoDB Atlas"

---

## F. DQ checklist (jangan sampai kena)

| Risiko | Cara hindari |
|--------|----------------|
| Video >3 menit | Hard cut di 2:55; export cek durasi |
| Tanpa Atlas live | Tampilkan Atlas browse + `atlas:true` di rehearsal |
| Mock data | Semua angka dari production URL |
| Tanpa write | Scene 3 & 4 wajib konfirmasi + `ya` |
| Tanpa subtitle EN | CapCut auto-caption + review |
| Nama Wargio | Sebut di VO awal & akhir |

---

## G. File terkait

| File | Fungsi |
|------|--------|
| `scripts/rehearsal_demo_video.sh` | Latihan curl semua query demo |
| `scripts/smoke_production.sh` | Health + 4 intent |
| `docs/devpost-submission.md` | Paste URL video setelah upload |

---

*Setelah upload: update README bagian Demo + checklist Hari 7 di `docs/todolist-harian-wargio.md`.*
