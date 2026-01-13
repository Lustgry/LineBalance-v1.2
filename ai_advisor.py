import requests
import urllib.parse
import json

def call_gimita_api(prompt_text):
    """
    Fungsi dasar untuk memanggil API Gimita ID via HTTP GET
    """
    try:
        # Encode prompt agar aman untuk URL
        encoded_prompt = urllib.parse.quote(prompt_text)
        
        # URL Endpoint API Gimita
        url = f"https://api.gimita.id/api/ai/gpt4?prompt={encoded_prompt}"
        
        # Kirim Request GET
        response = requests.get(url)
        
        # Cek status sukses (200 OK)
        if response.status_code == 200:
            try:
                data = response.json()
                
                # --- PERBAIKAN DI SINI ---
                # 1. Cek struktur: {'data': {'answer': 'TEKS JAWABAN'}} (Sesuai log error anda)
                if 'data' in data and isinstance(data['data'], dict) and 'answer' in data['data']:
                    return data['data']['answer']
                
                # 2. Cek struktur alternatif: {'content': 'TEKS JAWABAN'}
                elif 'content' in data:
                    return data['content']
                    
                # 3. Cek struktur alternatif: {'message': 'TEKS JAWABAN'}
                elif 'message' in data:
                    return data['message']
                
                # Jika format tidak dikenali, baru tampilkan mentahnya (untuk debugging)
                return str(data) 
                
            except ValueError:
                # Jika returnnya bukan JSON, tapi langsung text
                return response.text
        else:
            return f"Error API: Status Code {response.status_code}"
            
    except Exception as e:
        return f"Error Koneksi: {str(e)}"

def construct_context(method_name, cycle_time, efficiency, stations_data):
    data_str = ""
    for stn in stations_data:
        # format agar jelas bagi AI
        data_str += f"- {stn['Stasiun']}: Eff={stn['Efisiensi (%)']}%, Tugas=[ {stn['Daftar Tugas']} ]\n"
    
    context = f"""
    [DATA PERHITUNGAN]
    - Metode: {method_name}
    - Cycle Time: {cycle_time}
    - Efisiensi Total: {efficiency:.2f}%
    
    [DETAIL STASIUN & DESKRIPSI TUGAS]
    Format: ID_TUGAS (DESKRIPSI_PEKERJAAN)
    {data_str}
    """
    return context

def get_ai_suggestions(method_name, cycle_time, efficiency, stations_data):
    """
    Fitur AI: Analisis Otomatis
    """
    context = construct_context(method_name, cycle_time, efficiency, stations_data)
    
    prompt = f"""
    Anda adalah seorang analis ahli Line Balancing.
    Berikut adalah data hasil perhitungan saya:
    {context}
    
    PENTING:
    1. JANGAN mengasumsikan ini metode MDY(Moodie Young) atau LCR jika tertulis {method_name}.
    2. Fokus analisis pada data berikut:
    4. Perhatikan DESKRIPSI PEKERJAAN yang ada di dalam kurung (...) pada setiap tugas. 
       Gunakan deskripsi tersebut untuk memberikan saran yang logis secara teknis.
       (Contoh: Jika tugas 'Mengelas' dan 'Mengecat' ada di stasiun yang sama, apakah itu aman?)
    
    5. Identifikasi Bottleneck dan Idle Time.
    6. Berikan saran perbaikan konkret berdasarkan nama pekerjaan tersebut.
    {context}

    Tugasmu:
    1. Identifikasi Bottleneck.
    2. Identifikasi Idle Time.
    3. Berikan saran perbaikan profesional.
    4. Apakah perlu penambahan stasiun?
    5. Apakah metode line balancing yang digunakan sudah tepat? Jika tidak, metode apa
    
    Jawab dalam Bahasa Indonesia yang profesional.
    """
    return call_gimita_api(prompt)

def chat_with_data(user_question, context_string):
    """
    Fitur AI 2: Chatbot Interaktif
    """
    prompt = f"""
    Kamu adalah asisten dalam departement produksi yang membantu menganalisa stasiun hasil perhitungan Line Balancing.
    Gunakan data berikut sebagai acuan jawabanmu:
    {context_string}
    
    Pertanyaan User: {user_question}
    
    Jawablah pertanyaan user berdasarkan data di atas dengan singkat dan jelas.
    """
    return call_gimita_api(prompt)