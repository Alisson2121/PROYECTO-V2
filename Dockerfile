# Usa Python 3.11 slim
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código
COPY . .

# Exponer puerto para dashboard (opcional)
EXPOSE 8080

# Comando por defecto (se sobrescribe en fly.toml)
CMD ["python3", "bot_completo.py"]