# =====================================================================
#  SPK Rekomendasi Pair Trading  —  Metode AHP + SAW
#  Versi Python + Streamlit
#  Jalankan dengan:  streamlit run app.py
# =====================================================================

import streamlit as st
import pandas as pd

st.set_page_config(page_title="SPK AHP + SAW", layout="centered")

# ---------------------------------------------------------------------
# BAGIAN 0 — DATA AWAL & SESSION STATE
# Streamlit menjalankan ulang seluruh skrip setiap ada interaksi,
# jadi data yang harus "diingat" disimpan di st.session_state.
# ---------------------------------------------------------------------
if "criteria" not in st.session_state:
    st.session_state.criteria = [
        {"name": "Spread",            "type": "cost"},
        {"name": "Likuiditas",        "type": "benefit"},
        {"name": "Volatilitas",       "type": "benefit"},
        {"name": "Win-rate Backtest", "type": "benefit"},
        {"name": "Max Drawdown",      "type": "cost"},
    ]
if "alternatives" not in st.session_state:
    st.session_state.alternatives = ["XAUUSD", "EURUSD", "GBPJPY", "BTCUSD"]
if "values" not in st.session_state:
    st.session_state.values = {
        "XAUUSD": {"Spread": 3.5, "Likuiditas": 8,  "Volatilitas": 9,  "Win-rate Backtest": 55, "Max Drawdown": 20},
        "EURUSD": {"Spread": 1.0, "Likuiditas": 10, "Volatilitas": 4,  "Win-rate Backtest": 60, "Max Drawdown": 12},
        "GBPJPY": {"Spread": 2.5, "Likuiditas": 6,  "Volatilitas": 8,  "Win-rate Backtest": 52, "Max Drawdown": 25},
        "BTCUSD": {"Spread": 15,  "Likuiditas": 5,  "Volatilitas": 10, "Win-rate Backtest": 50, "Max Drawdown": 40},
    }

criteria     = st.session_state.criteria
alternatives = st.session_state.alternatives
values       = st.session_state.values


# ---------------------------------------------------------------------
# BAGIAN A — FUNGSI BANTU (konversi slider <-> skala Saaty)
# Posisi slider -8..8:  negatif = kriteria kiri lebih penting,
#                       positif = kriteria kanan lebih penting.
# ---------------------------------------------------------------------
def pos_to_value(p):
    if p == 0:
        return 1.0
    if p < 0:
        return abs(p) + 1          # kiri lebih penting -> nilai 2..9
    return 1 / (p + 1)             # kanan lebih penting -> nilai 1/2..1/9

CMP_WORDS = {2: "sedikit lebih penting", 3: "sedikit lebih penting",
             4: "cukup lebih penting",   5: "jelas lebih penting",
             6: "jelas lebih penting",   7: "sangat lebih penting",
             8: "sangat lebih penting",  9: "mutlak lebih penting"}

def describe(a, b, pos):
    v = pos_to_value(pos)
    if pos == 0:
        return f"{a} dan {b} sama penting"
    big  = v if v > 1 else 1 / v
    more = a if v > 1 else b
    less = b if v > 1 else a
    return f"{more} {CMP_WORDS.get(round(big), 'lebih penting')} daripada {less} (skala {round(big)})"


# ---------------------------------------------------------------------
# BAGIAN B — LOGIKA AHP  (menghasilkan bobot kriteria + uji CR)
# ---------------------------------------------------------------------
RI_TABLE = {2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24,
            7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}

def compute_ahp(matrix):
    n = len(matrix)
    if n < 2:
        return [1.0] * n, n, 0.0, 0.0

    # 1) jumlahkan tiap kolom
    col_sum = [sum(matrix[i][j] for i in range(n)) for j in range(n)]

    # 2) normalisasi kolom, lalu rata-ratakan tiap baris -> bobot
    weights = []
    for i in range(n):
        weights.append(sum(matrix[i][j] / col_sum[j] for j in range(n)) / n)

    # 3) uji konsistensi: lambda maks -> CI -> CR
    lam = 0.0
    for i in range(n):
        aw = sum(matrix[i][j] * weights[j] for j in range(n))
        lam += aw / weights[i]
    lam /= n
    CI = (lam - n) / (n - 1)
    RI = RI_TABLE.get(n, 1.49)
    CR = CI / RI if RI else 0.0
    return weights, lam, CI, CR


# ---------------------------------------------------------------------
# BAGIAN C — LOGIKA SAW  (menghasilkan ranking alternatif)
# ---------------------------------------------------------------------
def compute_saw(alternatives, criteria, values, weights):
    names = [c["name"] for c in criteria]
    types = {c["name"]: c["type"] for c in criteria}

    # nilai max (benefit) & min (cost) tiap kolom
    col_max, col_min = {}, {}
    for c in names:
        col = [values[a][c] for a in alternatives]
        col_max[c] = max(col) if col else 0
        nonzero = [x for x in col if x != 0]
        col_min[c] = min(nonzero) if nonzero else 0

    rows = []
    for a in alternatives:
        norm, score = {}, 0.0
        for idx, c in enumerate(names):
            x = values[a][c]
            if types[c] == "benefit":
                r = x / col_max[c] if col_max[c] else 0     # benefit: x / max
            else:
                r = col_min[c] / x if x else 0              # cost:   min / x
            norm[c] = r
            score += weights[idx] * r                       # Vi = Σ (w * r)
        rows.append({"alt": a, "score": score, "norm": norm})

    rows.sort(key=lambda t: t["score"], reverse=True)
    return rows


# =====================================================================
#  TAMPILAN
# =====================================================================
st.title("SPK Rekomendasi Pair Trading")
st.caption("Metode AHP (pembobotan kriteria) + SAW (perankingan alternatif)")

# ---------------------------------------------------------------------
# 1. KELOLA KRITERIA  (tambah / hapus, tipe cost / benefit)
# ---------------------------------------------------------------------
st.header("1. Kelola Kriteria")
for i, c in enumerate(criteria):
    col1, col2, col3 = st.columns([5, 3, 2])
    col1.write(c["name"])
    col2.write(f"`{c['type']}`")
    if col3.button("Hapus", key=f"delc{i}", disabled=len(criteria) <= 2):
        criteria.pop(i)
        st.rerun()

with st.form("add_criteria", clear_on_submit=True):
    c1, c2, c3 = st.columns([5, 3, 2])
    new_name = c1.text_input("Nama kriteria", label_visibility="collapsed",
                             placeholder="Nama kriteria baru")
    new_type = c2.selectbox("Tipe", ["benefit", "cost"], label_visibility="collapsed")
    if c3.form_submit_button("+ Tambah") and new_name:
        if new_name in [c["name"] for c in criteria]:
            st.warning("Nama kriteria harus unik.")
        else:
            criteria.append({"name": new_name, "type": new_type})
            for a in alternatives:                 # siapkan nilai default 0
                values[a][new_name] = 0.0
            st.rerun()

# ---------------------------------------------------------------------
# 2. KELOLA ALTERNATIF
# ---------------------------------------------------------------------
st.header("2. Kelola Alternatif")
for i, a in enumerate(alternatives):
    col1, col2 = st.columns([8, 2])
    col1.write(a)
    if col2.button("Hapus", key=f"dela{i}", disabled=len(alternatives) <= 2):
        alternatives.pop(i)
        values.pop(a, None)
        st.rerun()

with st.form("add_alt", clear_on_submit=True):
    c1, c2 = st.columns([8, 2])
    new_alt = c1.text_input("Nama alternatif", label_visibility="collapsed",
                            placeholder="Nama alternatif baru")
    if c2.form_submit_button("+ Tambah") and new_alt:
        if new_alt in alternatives:
            st.warning("Nama alternatif harus unik.")
        else:
            alternatives.append(new_alt)
            values[new_alt] = {c["name"]: 0.0 for c in criteria}
            st.rerun()

# ---------------------------------------------------------------------
# 3. PERBANDINGAN KEPENTINGAN KRITERIA (AHP)  — pakai slider
#    Sekaligus membangun matriks perbandingan n x n.
# ---------------------------------------------------------------------
st.header("3. Perbandingan Kepentingan Kriteria (AHP)")
st.caption("Geser ke arah kriteria yang lebih penting. Tengah = sama penting.")

n = len(criteria)
matrix = [[1.0] * n for _ in range(n)]      # diagonal = 1

for i in range(n):
    for j in range(i + 1, n):
        a, b = criteria[i]["name"], criteria[j]["name"]
        pos = st.slider(f"{a}  ↔  {b}", -8, 8, 0, key=f"cmp_{a}_{b}")
        st.caption(describe(a, b, pos))
        v = pos_to_value(pos)
        matrix[i][j] = v
        matrix[j][i] = 1 / v

weights, lam, CI, CR = compute_ahp(matrix)

# tampilkan bobot + status konsistensi
st.subheader("Bobot Kriteria")
bobot_df = pd.DataFrame({
    "Kriteria": [c["name"] for c in criteria],
    "Bobot (%)": [round(w * 100, 1) for w in weights],
})
st.bar_chart(bobot_df.set_index("Kriteria"))

if CR <= 0.10:
    st.success(f"λmaks = {lam:.3f} · CI = {CI:.3f} · CR = {CR*100:.1f}%  →  Konsisten (CR ≤ 10%)")
else:
    st.error(f"λmaks = {lam:.3f} · CI = {CI:.3f} · CR = {CR*100:.1f}%  →  Tidak konsisten (perbaiki perbandingan)")

# ---------------------------------------------------------------------
# 4. MATRIKS KEPUTUSAN (nilai mentah tiap alternatif)  — tabel editabel
# ---------------------------------------------------------------------
st.header("4. Matriks Keputusan")
st.caption("Masukkan nilai mentah tiap alternatif untuk tiap kriteria.")

crit_names = [c["name"] for c in criteria]
tabel = pd.DataFrame(
    [[values[a].get(c, 0.0) for c in crit_names] for a in alternatives],
    index=alternatives, columns=crit_names,
)
edited = st.data_editor(tabel, use_container_width=True)

# simpan kembali hasil edit ke session_state
for a in alternatives:
    for c in crit_names:
        values[a][c] = float(edited.loc[a, c])

# ---------------------------------------------------------------------
# 5. HASIL PERANKINGAN (SAW)
# ---------------------------------------------------------------------
st.header("5. Hasil Perankingan (SAW)")

hasil = compute_saw(alternatives, criteria, values, weights)

hasil_df = pd.DataFrame([{
    "Peringkat": i + 1,
    "Alternatif": r["alt"],
    **{c: round(r["norm"][c], 3) for c in crit_names},
    "Skor (Vi)": round(r["score"], 4),
} for i, r in enumerate(hasil)])

st.dataframe(hasil_df, use_container_width=True, hide_index=True)

if hasil:
    st.success(f"Rekomendasi teratas: {hasil[0]['alt']} (skor {hasil[0]['score']:.4f})")

st.download_button(
    "⬇ Ekspor hasil (CSV)",
    data=hasil_df.to_csv(index=False).encode("utf-8"),
    file_name="hasil-spk.csv",
    mime="text/csv",
)

