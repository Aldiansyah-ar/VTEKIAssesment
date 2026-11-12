# README — Case 3: Enterprise Knowledge Chatbot (SkyWings Airlines)

Chatbot internal berbasis **Retrieval-Augmented Generation (RAG)** yang menjawab pertanyaan karyawan/pelanggan hanya dari dokumen yang disetujui, dengan **sitasi wajib**, **penolakan aman** saat informasi tidak tersedia, **kontrol akses berbasis peran (RBAC)**, dan **guardrail terhadap prompt injection**.

Knowledge base contoh menggunakan `luggage_policy.txt` (publik) dan `internal_baggage_ops.txt` (staff-only, sintetis) milik maskapai fiktif **SkyWings Airlines**.

---

## ⚙️ Setup

**Prasyarat:** Python 3.10+.

```bash
cd case3
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt