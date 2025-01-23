FROM gcr.io/distroless/python3-debian12 AS base
ARG TARGETARCH

FROM base AS amd64
ENV ARCH x86_64

FROM base AS arm64
ENV ARCH aarch64


FROM python:3.11-slim-bookworm AS build

# Install OpenCV's runtime dependencies
RUN apt-get update && \
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
build-essential libgl1-mesa-dev libopencv-dev \
&& rm -rf /var/lib/apt/lists/* && apt-get clean && apt-get autoclean && apt-get autoremove

WORKDIR /tmp
COPY requirements.txt /tmp
RUN python -m pip install --upgrade pip setuptools \
&& pip install --no-cache-dir -r requirements.txt


FROM ${TARGETARCH} AS prod

# site-packagesをコピー
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/lib/python3.11/dist-packages

WORKDIR /app
COPY ./app /app/app
COPY ./key /app/key
COPY ./.env /app/.env

EXPOSE 8004
ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8004"]
