FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# We don't expose ports, this just runs in the background.
CMD ["python", "-u", "healer.py"]
