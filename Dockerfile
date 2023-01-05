# FROM tiangolo/uvicorn-gunicorn:python3.9-alpine3.14
FROM python:3-slim-buster

RUN apt-get update -y && apt-get upgrade -y

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN mkdir /var/ocreniisan
COPY . /var/ocreniisan
WORKDIR /var/ocreniisan

EXPOSE 8004
CMD ["uvicorn", "ocreniisan.main:app", "--reload", "--host", "0.0.0.0", "--port", "8004"]
