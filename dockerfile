# Verwende ein offizielles Python-Image
FROM python:3.10-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere die Dateien in den Container
COPY . /app

# Installiere Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Exponiere den Port
EXPOSE 5000

# Befehl zum Starten der App
CMD ["python", "app.py"]
