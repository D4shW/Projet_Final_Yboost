FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

# Init de la DB au lancement (pas au build) — sinon le volume monté écrase la DB
CMD ["sh", "-c", "python init_db.py && python api.py"]
