FROM python:3.11-slim-buster AS build

RUN apt-get update -y && apt-get upgrade -y && \
apt-get install --no-install-recommends build-essential -y

WORKDIR /app
COPY requirements.txt /app
RUN python -m pip install --upgrade pip setuptools && \
pip install --no-cache-dir -r requirements.txt


FROM python:3.11-slim-buster

RUN apt-get update -y && apt-get upgrade -y && \
apt-get install --no-install-recommends libgl1-mesa-dev libopencv-dev -y && \
rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get autoclean && apt-get autoremove

COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
RUN pip install --upgrade --no-deps --force-reinstall uvicorn
EXPOSE 8004

WORKDIR /var/ocreniisan
COPY . /var/ocreniisan
CMD ["uvicorn", "ocreniisan.main:app", "--reload", "--host", "0.0.0.0", "--port", "8004"]
