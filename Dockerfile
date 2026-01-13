# 1. Gunakan Python versi 3.10 yang ringan (Slim)
FROM python:3.10-slim

# 2. Set folder kerja di dalam container
WORKDIR /app

# 3. [PENTING] Install Graphviz System (Bukan cuma library Python)
# Tanpa baris ini, Grafik.py akan error "dot not found"
RUN apt-get update && apt-get install -y \
    graphviz \
    && rm -rf /var/lib/apt/lists/*
    
# 4. Salin requirements & Install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Salin kode program DAN folder .streamlit
COPY . .

# 6. Buka Port
EXPOSE 8501

# 7. Jalankan (Perintahnya jadi pendek karena config ada di file .toml)
CMD ["streamlit", "run", "app.py"]