FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

ENV PYTHONPATH=/app
ENV FLASK_APP=src/app.py
ENV FLASK_ENV=production

EXPOSE 8083

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8083"] 