import pandas as pd
import os

# === Baca file Excel ===
file_path = "kalimantan.xlsx"
df = pd.read_excel(file_path, header=1)

# === Pilih kolom yang dibutuhkan ===
df_clean = df[[
    'SITE ID',
    'PROVINSI',
    'KAB_KOTA',
    'NAMA_LOKASI',
    'KECAMATAN',
    'DESA',
    'ALAMAT LENGKAP',
    'LATITUDE',
    'LONGITUDE',
    'CONTACT NAME',
    'CONTACT PHONE',
    'REKOMENDASI BAND ALOC',
    'REKOMENDASI PERANGKAT',
    'REKOMENDASI PERANGKAT MODEM',
    'REKOMENDASI PERANGKAT TRANSCEIVER',
    'TEKNISI',
    'STATUS',
]].dropna(subset=['LATITUDE', 'LONGITUDE'])

# === Buat kolom gabungan Nama_Lokasi_Lengkap ===
df_clean['Nama_Lokasi_Lengkap'] = (
    df_clean['PROVINSI'].astype(str) + " - " +
    df_clean['KAB_KOTA'].astype(str) + " - " +
    df_clean['NAMA_LOKASI'].astype(str)
)

# === Folder output ===
output_dir = "output_mymaps"
os.makedirs(output_dir, exist_ok=True)

# === Simpan per provinsi ===
for prov, group in df_clean.groupby('PROVINSI'):
    filename = f"{output_dir}/lokasi_{prov.replace(' ', '_')}.csv"
    group.to_csv(filename, index=False, encoding='utf-8')
    print(f"✅ File untuk {prov} disimpan: {filename}")

print("\n🎯 Semua file siap di-upload ke Google My Maps!")
print("💡 Kolom 'Nama_Lokasi_Lengkap' akan tampil sebagai label di peta.")
