# Use a specific, stable Python version — NOT 3.14, since several of our
# dependencies (torch/whisper) have better-tested wheels on 3.11.
FROM python:3.11-slim

# ffmpeg is needed by both Whisper and our webm->wav conversion step
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (separate layer = faster rebuilds
# when only your code changes, not your dependencies)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the actual application code
COPY . .

# Seed the database at build time so orders.db exists in the image
RUN python data/seed_db.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]