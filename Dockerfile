# FROM tiangolo/uvicorn-gunicorn:python3.9-alpine3.14
FROM python:3-slim-buster

RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install build-essential -y
RUN apt-get install libgl1-mesa-dev -y
RUN apt-get install libopencv-dev -y

RUN python -m pip install --upgrade pip setuptools
RUN mkdir /var/ocreniisan
COPY . /var/ocreniisan
WORKDIR /var/ocreniisan
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8004
CMD ["uvicorn", "ocreniisan.main:app", "--reload", "--host", "0.0.0.0", "--port", "8004"]
