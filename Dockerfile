# Usa una versión ligera de Python 3.12
FROM python:3.12-slim

# Crea una carpeta de trabajo dentro de la "caja"
WORKDIR /app

# Copia los archivos de tu PC a la "caja"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expone el puerto 8000 para que podamos entrar a la API
EXPOSE 8000

# Comando para encender el servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]