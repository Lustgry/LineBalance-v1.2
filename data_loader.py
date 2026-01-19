import pandas as pd
import math

def clean_id(val):
    """
    Mengubah input apapun (int, float, str) menjadi String bersih.
    Contoh: 
    - 1     -> "1"
    - 1.0   -> "1" 
    - " A " -> "A"
    """
    if pd.isna(val):
        return ""
    
    # Ubah ke string
    s_val = str(val).strip()
    
    # Hapus akhiran .0 jika itu angka desimal (misal 1.0 jadi 1)
    if s_val.endswith('.0'):
        s_val = s_val[:-2]
        
    return s_val.upper()

def load_data(uploaded_file):
    try:
        # 1. Buka File Excel
        df = pd.read_excel(uploaded_file)
        
        # 2. Normalisasi Nama Kolom (Biar user bebas kasih nama apa aja)
        # Kita buat kamus sinonim
        col_mapping = {}
        for col in df.columns:
            clean_col = str(col).strip().upper()
            
            # Sinonim untuk TASK
            if clean_col in ['TASK', 'TUGAS', 'ID', 'NO', 'AKTIVITAS', 'ACTIVITY']:
                col_mapping[col] = 'Task'
            
            # Sinonim untuk TIME
            elif clean_col in ['TIME', 'WAKTU', 'DURASI', 'DURATION', 'SECONDS', 'DETIK']:
                col_mapping[col] = 'Time'
                
            # Sinonim untuk PREDECESSORS
            elif clean_col in ['PREDECESSORS', 'PREDECESSOR', 'PENDAHULU', 'SYARAT', 'PRED']:
                col_mapping[col] = 'Precedence'
                
            # Sinonim untuk DESKRIPSI
            elif clean_col in ['DESKRIPSI', 'DESCRIPTION', 'DESC', 'KET', 'KETERANGAN', 'NAMA TUGAS']:
                col_mapping[col] = 'Description'

        # Rename kolom sesuai standar kita
        df = df.rename(columns=col_mapping)

        # 3. Validasi Kolom Wajib
        required_cols = ['Task', 'Time', 'Precedence']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return None, f"Kolom wajib tidak ditemukan: {', '.join(missing)}. Pastikan nama kolom di Excel benar."

        # 4. Bersihkan Kolom 'Task' (Ubah angka jadi teks)
        df['Task'] = df['Task'].apply(clean_id)

        # 5. Bersihkan Kolom 'Time' (Pastikan angka)
        df['Time'] = pd.to_numeric(df['Time'], errors='coerce').fillna(0)

        # 6. Bersihkan Kolom 'Predecessors'
        def clean_preds(val):
            # Jika kosong/NaN, kembalikan list kosong
            if pd.isna(val) or str(val).strip() == '' or str(val).strip() == '-':
                return []
            
            val_str = str(val)
            # Ganti pemisah aneh-aneh jadi koma
            val_str = val_str.replace(';', ',').replace('|', ',')
            
            parts = val_str.split(',')
            cleaned = []
            for p in parts:
                p_clean = clean_id(p) # Pakai fungsi pembersih yang sama dgn Task ID
                if p_clean and p_clean not in ['0', 'NONE', 'NAN', 'NA']:
                    cleaned.append(p_clean)
            return cleaned

        df['Precedence'] = df['Precedence'].apply(clean_preds)

        # 7. Handle Kolom Deskripsi (Opsional)
        if 'Description' not in df.columns:
            # Kalau tidak ada, kita buat kolom kosong biar codingan lain gak error
            df['Description'] = "-"
        else:
            df['Description'] = df['Description'].astype(str).fillna("-")

        # Kembalikan data sbg Dictionary
        return df.to_dict('records'), None

    except Exception as e:
        return None, f"Gagal membaca file: {str(e)}"