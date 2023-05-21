FROM python:3.8
WORKDIR /usr/src/app
COPY ./manager .
COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["python3","main.py"]