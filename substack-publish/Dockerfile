FROM python:3-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY publish.py .

ENTRYPOINT ["python", "publish.py"]
