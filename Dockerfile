FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

COPY . /app
RUN pip install --no-cache-dir -r /app/requirements.txt
WORKDIR /app

EXPOSE 8000
CMD ["python3", "main.py"]