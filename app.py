import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import streamlit.components.v1 as components
import base64
import re
#Tambahan Revisi
from Flow import create_line_flow, create_precedence_diagram

# Import fungsi perhitungan metode
from methods.lcr import solve_lcr
from methods.rpw import solve_rpw
from methods.mdy import solve_mdy
from Flow import create_line_flow
from data_loader import load_data

# Import modul AI  (Gimita)
from ai_advisor import get_ai_suggestions, chat_with_data, construct_context

# KONFIGURASI HALAMAN 
st.set_page_config(page_title="Line Balancing App", layout="wide")

# SESSION STATE
if 'hasil_perhitungan' not in st.session_state:
    st.session_state['hasil_perhitungan'] = None
if 'metode_terpilih' not in st.session_state:
    st.session_state['metode_terpilih'] = ""
# State untuk Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# JUDUL 
st.title("Line Balancing Calculator")
st.markdown("Aplikasi optimasi lintasan produksi dengan AI Assistant.")
st.divider()

# SIDEBAR: INPUT 
st.sidebar.header("1. Input Data")
uploaded_file = st.sidebar.file_uploader("Upload Excel (.xlsx) Note: Pastikan Data mengandung 3 Kolom (Task, Time, Precedence, dan Description (Optional)).", type=["xlsx"])

# (Input API Key Gimita )

if uploaded_file is not None:
    # Load Data
    data, error_msg = load_data(uploaded_file)
    
    if error_msg:
        st.error(f" Terjadi Kesalahan: {error_msg}")
    else:
        # --- PARAMETER ---
        st.sidebar.header("2. Parameter")
        max_task_time = max([t['Time'] for t in data])
        
        cycle_time = st.sidebar.number_input(
            "Cycle Time (Detik/Menit)", 
            min_value=int(max_task_time), 
            value=max(10, int(max_task_time)),
            help="Cycle Time tidak boleh lebih kecil dari waktu tugas terpanjang."
        )
        
        st.sidebar.header("3. Metode")
        method_option = st.sidebar.selectbox(
            "Pilih Algoritma", 
            ["LCR (Largest Candidate Rule)", "RPW (Ranked Positional Weight)", "MDY (Moodie Young)"]
        )
        
        # Tombol Hitung
        if st.sidebar.button("Hitung Keseimbangan"):
            # Reset Chat History saat hitung ulang agar konteks baru
            st.session_state.messages = []
            
            result = []
            if "LCR" in method_option:
                result = solve_lcr(data, cycle_time)
            elif "RPW" in method_option:
                result = solve_rpw(data, cycle_time)
            elif "MDY" in method_option:
                result = solve_mdy(data, cycle_time)
            
            st.session_state['hasil_perhitungan'] = result
            st.session_state['metode_terpilih'] = method_option
            st.rerun()

        # TAMPILAN DATA MENTAH 
        with st.expander("Lihat Data Input Mentah", expanded=True):
            # Buat copy data untuk ditampilkan
            df_view = pd.DataFrame(data)
            
            # Rapikan tampilan Precedence (List -> String)
            df_view['Precedence'] = df_view['Precedence'].apply(lambda x: ", ".join(x) if x else "-")
            
            # Atur urutan kolom agar enak dilihat
            cols_order = ['Task', 'Description', 'Time', 'Precedence']
            # Hanya ambil kolom yang benar-benar ada
            cols_to_show = [c for c in cols_order if c in df_view.columns]
            
            st.dataframe(df_view[cols_to_show], width=None, use_container_width=True)

        #Tambahan Revisi (Visual Diagram Presedence Untuk data imput)

        with st.expander(" Lihat Precedence Diagram data imput", expanded=False):
            st.caption("Visualisasi Precedence Diagram tugas sebelum perhitungan.")
            
            # 1. Buat 
            pdm_graph = create_precedence_diagram(data)
            
            try:
                # Render SVG untuk Tampilan
                pdm_svg = pdm_graph.pipe(format='svg').decode('utf-8')
                # Bersihkan width/height agar responsif
                pdm_svg = re.sub(r'(width|height)="[^"]*"', '', pdm_svg)
                
                # Render PNG untuk Download
                pdm_png = pdm_graph.pipe(format='png')
                pdm_b64 = base64.b64encode(pdm_png).decode("utf-8")

                # Tampilkan
                st.image(pdm_png, caption="Precedence Diagram", use_container_width=False, width=None)
                
                # Tombol Download
                href = f'<a href="data:image/png;base64,{pdm_b64}" download="precedence_diagram.png" style="text-decoration: none; padding: 10px 20px; background-color: #4CAF50; color: white; border-radius: 5px; font-weight: bold;">Download Diagram</a>'
                st.markdown(href, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Gagal membuat Precedence Diagram: {e}")
                st.warning("Pastikan 'graphviz' terinstall di sistem (apt-get install graphviz).")

        st.divider()
        
        # TAMPILAN HASIL 
        hasil = st.session_state['hasil_perhitungan']
        metode = st.session_state['metode_terpilih']

        if hasil is not None:
            st.divider()
            
            if isinstance(hasil, str):
                st.error(f"Gagal: {hasil}")
            else:
                st.subheader(f" Hasil Perhitungan: {metode}")
                
                # SIAPKAN DATA RINGKASAN DENGAN DESKRIPSI (Perbaikan)
                summary_data = []
                for stn in hasil:
                    waktu_terpakai = cycle_time - stn['time_left']
                    efisiensi_stasiun = (waktu_terpakai / cycle_time) * 100
                    
                    # LOGIKA BARU: Gabungkan ID Tugas + Deskripsi
                    task_labels = []
                    for t_id in stn['tasks']:
                        # Cari data asli yang cocok dengan ID tugas ini
                        # Kita cari di variabel 'data' (hasil load_data)
                        original_task = next((item for item in data if str(item['Task']) == str(t_id)), None)
                        
                        desc = ""
                        if original_task and 'Description' in original_task:
                             # Cek kalau deskripsinya bukan strip (-) atau kosong
                            if original_task['Description'] not in ['-', '', 'nan', 'None']:
                                desc = f" ({original_task['Description']})"
                        
                        # Hasilnya jadi: "1 (Potong Kawat)" atau "A (Las)"
                        task_labels.append(f"{t_id}{desc}")

                    summary_data.append({
                        "Stasiun": f"Stasiun {stn['id']}",
                        "Daftar Tugas": ", ".join(task_labels), # <--- Ini yang dikirim ke AI
                        "Waktu Terpakai": waktu_terpakai,
                        "Idle Time": stn['time_left'],
                        "Efisiensi (%)": round(efisiensi_stasiun, 1)
                    })
                
                df_summary = pd.DataFrame(summary_data)

               # Hitung Metrik Global
                num_stations = len(hasil)
                total_time_used = df_summary["Waktu Terpakai"].sum()
                global_efficiency = (total_time_used / (num_stations * cycle_time)) * 100
                balance_delay = 100 - global_efficiency

                # --- TAMBAHAN: HITUNG SMOOTHING INDEX (SI) ---
                # Rumus: Akar dari jumlah kuadrat (Cycle Time - Waktu Stasiun)
                smoothing_index = ((cycle_time - df_summary["Waktu Terpakai"]) ** 2).sum() ** 0.5
                
                # KPI (Key Performance Indicator)
                # Ubah kolom dari 4 menjadi 5 untuk memuat Smoothing Index
                c1, c2, c3, c4, c5 = st.columns(5) 
                
                c1.metric("Jumlah Stasiun", num_stations)
                c2.metric("Cycle Time", cycle_time)
                c3.metric("Efisiensi Lintasan", f"{global_efficiency:.1f}%")
                c4.metric("Balance Delay", f"{balance_delay:.1f}%")
                
                # Tampilkan Smoothing Index (Semakin kecil semakin baik, 0 = sempurna)
                c5.metric("Smoothing Index", f"{smoothing_index:.2f}", help="Indikator kelancaran aliran. Nilai mendekati 0 berarti keseimbangan sempurna.")

                st.divider()
                # (FITUR BARU) FLOW 

                st.divider()
                st.subheader("Visualisasi Alur Stasiun (Interaktif)")
                st.info("Scroll untuk Zoom In/Out. Klik & Tahan untuk menggeser sepuasnya.")
                

                # 1. Generate Graph Object
                graph = create_line_flow(hasil, data, cycle_time)
                
                try:
                    # A. PROSES UNTUK TAMPILAN LAYAR (SVG) 
                    # Kita tetap butuh SVG untuk ditampilkan di layar agar fitur Zoom lancar
                    svg_raw = graph.pipe(format='svg').decode('utf-8')
                    
                    # Bersihkan atribut width/height kaku agar responsif
                    svg_code = re.sub(r'(width|height)="[^"]*"', '', svg_raw)
                    if '<svg' in svg_code:
                        svg_code = svg_code.replace('<svg', '<svg style="width: 100%; height: 100%;" ', 1)

                    # B. PROSES UNTUK DOWNLOAD (PNG) 
                    # Di sini kita minta Graphviz merender ulang menjadi PNG 
                    png_bytes = graph.pipe(format='png')
                    
                    # Encode ke Base64 agar bisa dimasukkan ke tombol HTML
                    png_b64 = base64.b64encode(png_bytes).decode("utf-8")

                except Exception as e:
                    st.error(f"Gagal render Graphviz: {e}")
                    svg_code = ""
                    png_b64 = ""

                # 3. Buat Kode HTML + JavaScript (Tombol Download PNG)
                if svg_code and png_b64:
                    
                    html_block = f"""
                    <style>
                        /* Container Luar */
                        .viz-container {{
                            border: 2px solid #444; 
                            border-radius: 12px; 
                            background-color: #0E1117; 
                            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
                            overflow: hidden; 
                            display: flex;
                            flex-direction: column;
                            font-family: sans-serif; /* Pastikan container pakai font standar */
                        }}
                        
                        .viz-header {{
                            padding: 8px 15px;
                            background: #1F2937;
                            border-bottom: 1px solid #444;
                            text-align: right;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        }}

                        .viz-title {{
                            color: #aaa;
                            font-family: sans-serif;
                            font-size: 12px;
                            font-weight: bold;
                        }}

                        /* Tombol Download Style Baru */
                        .btn-dl {{
                            background: #2563EB; 
                            color: white;
                            padding: 6px 15px; 
                            border-radius: 6px;
                            text-decoration: none; 
                            font-size: 14px; /* Ukuran font disesuaikan sedikit */
                            font-weight: 600; /* Ketebalan font standar */
                            font-family: "Source Sans Pro", sans-serif; /* <--- INI KUNCINYA (Font Streamlit) */
                            transition: 0.2s;
                            display: inline-block;
                            border: 1px solid #2563EB;
                        }}
                        .btn-dl:hover {{ 
                            background: #1D4ED8; 
                            color: white; 
                            border-color: #1D4ED8;
                        }}

                        /* Area Gambar */
                        #svg-container {{
                            width: 100%;
                            height: 450px; /* Tinggi Jendela */
                            cursor: grab;
                            background-color: #0E1117; 
                        }}
                        #svg-container:active {{ cursor: grabbing; }}
                    </style>

                    <div class="viz-container">
                        <div class="viz-header">
                            <span class="viz-title">ZOOM & PAN VIEW</span>
                            <a href="data:image/png;base64,{png_b64}" download="line_balancing_result.png" class="btn-dl">
                                Unduh PNG
                            </a>
                        </div>
                        
                        <div id="svg-container">
                            {svg_code}
                        </div>
                    </div>

                    <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
                    <script>
                        setTimeout(function() {{
                            var svgEl = document.querySelector('#svg-container svg');
                            if (svgEl) {{
                                svgPanZoom(svgEl, {{
                                    zoomEnabled: true,
                                    controlIconsEnabled: true,
                                    fit: true,
                                    center: true,
                                    minZoom: 0.1,
                                    maxZoom: 20,
                                    contain: false 
                                }});
                            }}
                        }}, 500);
                    </script>
                    """
                    
                    # Tinggi Frame Streamlit 
                    components.html(html_block, height=500)
                
                # ... (Kode Grafik Batang plt.subplots Anda yang lama ada di bawah sini) ...

                # GRAFIK 
                st.write("### Grafik Beban Kerja")
                
                # UKURAN DINAMIS
                # Hitung lebar grafik berdasarkan jumlah stasiun. 
                # Min lebar 10, tapi jika stasiun banyak, lebar ditambah 0.8 per stasiun
                num_stations = len(df_summary)
                fig_width = max(10, num_stations * 0.8) 
                
                fig, ax = plt.subplots(figsize=(fig_width, 6)) # Tinggi sedikit dinaikkan agar label muat
                
                bars = ax.bar(df_summary['Stasiun'], df_summary['Waktu Terpakai'], color='#2E86C1', zorder=3)
                ax.axhline(y=cycle_time, color='red', linestyle='--', linewidth=2, label=f'Cycle Time ({cycle_time})', zorder=4)
                
                ax.set_ylabel("Waktu")
                ax.set_title("Distribusi Waktu Stasiun Kerja", fontsize=14)
                ax.legend(loc='lower right')
                ax.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)

                # LABEL TIDAK DEMPET 
                # Putar label sumbu X sebesar 45 derajat dan rapikan layout
                plt.xticks(rotation=45, ha='right')
                
                # Menambahkan label angka di atas batang
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + (cycle_time * 0.02),
                            f'{height}', ha='center', va='bottom', fontsize=9, fontweight='bold')
                
                # Penting agar label yang diputar tidak terpotong saat dirender
                plt.tight_layout() 
                
                st.pyplot(fig)

                # TOMBOL DOWNLOAD 
                # Simpan plot ke dalam buffer memori
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches='tight', dpi=300)
                buf.seek(0)
                
                col_dl, _ = st.columns([1, 4])
                with col_dl:
                    st.download_button(
                        label="Unduh Grafik",
                        data=buf,
                        file_name=f"grafik_line_balancing_{metode}.png",
                        mime="image/png"
                    )

                # TABEL
                st.write("### 📑 Rincian Tabel")
                st.dataframe(
                    df_summary.style.background_gradient(subset=['Efisiensi (%)'], cmap="RdYlGn"),
                    width='stretch'
                )

                # BAGIAN 1: AI Analisis Otomatis ---
                st.divider()
                st.subheader("Analisa Otomatis")
                
                if st.button("Minta Analisis Cepat "):
                    with st.spinner("Menghubungi Gimita AI..."):
                        saran = get_ai_suggestions(
                            method_name=metode,
                            cycle_time=cycle_time,
                            efficiency=global_efficiency,
                            stations_data=summary_data
                        )
                        st.success("Analisis Selesai!")
                        st.info(saran)

                # BAGIAN 2: CHATBOT INTERAKTIF ---
                st.divider()
                st.subheader("💬 Chat Ai")
                st.caption("Tanyakan apa saja mengenai hasil perhitungan di atas.")

                # Tampilkan riwayat chat
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                # Input Chat User
                if prompt := st.chat_input("Contoh: Stasiun mana yang paling sibuk?"):
                    # Simpan pesan user
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)

                    # Proses Jawaban AI
                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        message_placeholder.markdown("Sedang mengetik...")
                        
                        # Bangun konteks data terkini
                        context_str = construct_context(metode, cycle_time, global_efficiency, summary_data)
                        
                        # Panggil API Gimita untuk Chat
                        full_response = chat_with_data(prompt, context_str)
                        
                        message_placeholder.markdown(full_response)
                    
                    # Simpan jawaban AI
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

else:
    st.info("Upload file Excel untuk memulai.")