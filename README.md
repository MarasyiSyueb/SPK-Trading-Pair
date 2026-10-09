# SPK-Trading-Pair
# SPK Rekomendasi Pair Trading — Metode AHP + SAW

Sistem Pendukung Keputusan (SPK) berbasis web untuk merekomendasikan pasangan/instrumen
trading terbaik. Aplikasi mengombinasikan dua metode *Multi-Criteria Decision Making* (MCDM):

- **AHP (Analytic Hierarchy Process)** — menghitung **bobot** tiap kriteria melalui
  perbandingan berpasangan, lengkap dengan uji konsistensi (*Consistency Ratio*).
- **SAW (Simple Additive Weighting)** — melakukan **perankingan** alternatif berdasarkan
  bobot tersebut.

Dibangun dengan **Python + Streamlit**.

---

##Menjalankan Secara Lokal

```bash
# 1. (opsional) buat virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. pasang dependensi
pip install -r requirements.txt

# 3. jalankan aplikasi
streamlit run app.py
```

Aplikasi akan terbuka otomatis di browser pada `http://localhost:8501`.

---


## Disusun oleh:

- Nama: Muhamad Mar'asyi Syueb
- NIM: 25/572971/PPA/07205

