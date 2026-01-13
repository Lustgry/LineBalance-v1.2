import graphviz
import html
import random

def create_line_flow(hasil_perhitungan, data_asli, cycle_time):
    """
    Membuat diagram alur stasiun kerja dengan tampilan JUMBO:
    - Kotak Lebih Besar (Padding diperbesar).
    - Font Lebih Besar (Judul 20pt, Isi 16pt).
    - Garis Tebal & Solid.
    - Anti-Crash.
    """
    
    # 1. Konfigurasi Global
    dot = graphviz.Digraph(comment='Line Balancing Flow')
    
    dot.attr(rankdir='LR')           # Kiri ke Kanan
    dot.attr(splines='polyline')     # Garis patah-patah tegas
    dot.attr(bgcolor='transparent')  
    
    # [PERBAIKAN JARAK]: Karena kotak makin besar, jarak harus makin jauh
    dot.attr(ranksep='3.0')          # Jarak horizontal diperlebar lagi
    dot.attr(nodesep='2.5')          # Jarak vertikal diperlebar lagi
    dot.attr(margin='0')              

    # Setting Default Node & Edge
    dot.attr('node', fontname='Arial', shape='plain', fontcolor='white') 
    # Arrowsize disesuaikan agar imbang dengan kotak besar
    dot.attr('edge', arrowsize='2.5', fontname='Arial') 

    # --- PALET WARNA NEON ---
    edge_colors = [
        '#FF3D00', '#D500F9', '#00B0FF', '#00E676', 
        '#FFAB00', '#F50057', '#651FFF'
    ]

    # --- 2. MAPPING LOKASI TUGAS ---
    task_location = {} 
    for stn in hasil_perhitungan:
        st_id = f"S{stn['id']}"
        for t in stn['tasks']:
            task_location[str(t)] = st_id

    # BUAT KOTAK STASIUN 
    for stn in hasil_perhitungan:
        stasiun_id = str(stn['id'])
        node_id = f"S{stasiun_id}"
        
        waktu_terpakai = cycle_time - stn['time_left']
        eff = (waktu_terpakai / cycle_time) * 100
        
        # Logika Warna Header Box
        if eff < 70:
            border_color = '#FFD700' 
            header_bg = '#FF8F00'     
        elif eff > 95:
            border_color = '#00E676' 
            header_bg = '#00C853'     
        else:
            border_color = '#29B6F6' 
            header_bg = '#0277BD'     

        body_bg = '#212121' 

        # SUSUN BARIS TUGAS (FONT BESAR) 
        rows_html = ""
        for t_id in stn['tasks']:
            clean_t_id = html.escape(str(t_id))
            original = next((item for item in data_asli if str(item['Task']) == str(t_id)), None)
            desc_text = ""
            
            if original and str(original.get('Description', '-')) not in ['-', 'nan', '', 'None']:
                raw_desc = str(original['Description'])
                short_desc = raw_desc[:25] + ".." if len(raw_desc) > 25 else raw_desc
                safe_desc = html.escape(short_desc)
                # Saya naikkan font deskripsi jadi 14 agar seimbang dengan Task ID yg 16
                desc_text = f"<I><FONT POINT-SIZE='14' COLOR='#b0b0b0'> ({safe_desc})</FONT></I>"
            
            # Padding 6 & Font 16 sesuai request
            rows_html += f"""
            <tr>
                <td align='left' cellpadding='6'>
                    <FONT POINT-SIZE="16"><B>• {clean_t_id}</B></FONT> 
                    {desc_text}
                </td>
            </tr>
            """

        # TABEL UTAMA 
        label_html = f"""<
        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0">
            <TR>
                <TD BGCOLOR="{body_bg}" BORDER="6" COLOR="{border_color}" CELLPADDING="10">
                    
                    <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" BGCOLOR="{body_bg}">
                        <TR>
                            <TD PORT="n" ALIGN="CENTER" CELLPADDING="15" BGCOLOR="{header_bg}">
                                <FONT COLOR="white" POINT-SIZE="20"><B>STASIUN {stasiun_id}</B></FONT>
                            </TD>
                        </TR>
                        <TR>
                            <TD ALIGN="CENTER" BORDER="2" SIDES="B" COLOR="#555555" CELLPADDING="10">
                                <FONT COLOR="#e0e0e0" POINT-SIZE="14">Target: {cycle_time} | Pakai: {waktu_terpakai}</FONT><BR/>
                                <FONT COLOR="{border_color}" POINT-SIZE="16"><B>Eff: {eff:.1f}%</B></FONT>
                            </TD>
                        </TR>
                        <TR>
                            <TD PORT="s" ALIGN="LEFT" CELLPADDING="10">
                                <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="5">
                                    {rows_html}
                                </TABLE>
                            </TD>
                        </TR>
                    </TABLE>
                </TD>
            </TR>
        </TABLE>
        >"""
        dot.node(node_id, label=label_html)

    # --- 4. GARIS PENGHUBUNG (FLOW UTAMA) ---
    ids = [f"S{stn['id']}" for stn in hasil_perhitungan]
    for i in range(len(ids) - 1):
        # Jalur Utama Tebal
        dot.edge(ids[i], ids[i+1], 
                 color='#9E9E9E', 
                 penwidth='6.0',       # Dipertebal jadi 6.0 agar imbang dengan border
                 minlen='2',           
                 tailport='e', 
                 headport='w')

    # GARIS PENGHUBUNG (Predecessor Flow) 
    connections = set()
    color_index = 0  
    
    for stn in hasil_perhitungan:
        current_node_id = f"S{stn['id']}"
        
        for t_id in stn['tasks']:
            task_data = next((item for item in data_asli if str(item['Task']) == str(t_id)), None)
            
            if task_data and 'Predecessors' in task_data:
                preds = task_data['Predecessors']
                if isinstance(preds, str): 
                    preds = [p.strip() for p in preds.split(',')]
                
                for p in preds:
                    source_node_id = task_location.get(str(p))
                    
                    if source_node_id and source_node_id != current_node_id:
                        
                        # [PENGAMAN]
                        try:
                            src_idx = int(source_node_id[1:])
                            curr_idx = int(current_node_id[1:])
                        except:
                            continue 

                        # Jika loncat > 1 stasiun
                        if curr_idx > src_idx + 1: 
                            conn = (source_node_id, current_node_id)
                            if conn not in connections:
                                used_color = edge_colors[color_index % len(edge_colors)]
                                color_index += 1
                                
                                dot.edge(source_node_id, current_node_id, 
                                         color=used_color,       
                                         style='solid',          
                                         penwidth='4.0',         # Dipertebal jadi 4.0
                                         constraint='false',
                                         tailport='se', 
                                         headport='sw', 
                                         label=''
                                )
                                connections.add(conn)

    return dot