FROM gcr.io/distroless/python3-debian11 AS base
ARG TARGETARCH

FROM base AS amd64
ENV ARCH x86_64

FROM base AS arm64
ENV ARCH aarch64


FROM python:3.9-slim-buster AS build

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

# OpenCVに必要なファイルコピー
COPY --from=build /lib/${ARCH}-linux-gnu/libm-2.28.so /lib/${ARCH}-linux-gnu/libm-2.28.so
COPY --from=build /lib/${ARCH}-linux-gnu/libpcre.so.3 /lib/${ARCH}-linux-gnu/libpcre.so.3
COPY --from=build /usr/lib/${ARCH}-linux-gnu/libGL.so.1 /usr/lib/${ARCH}-linux-gnu/libGL.so.1
COPY --from=build /usr/lib/${ARCH}-linux-gnu/libglib-2.0.so.0 /usr/lib/${ARCH}-linux-gnu/libglib-2.0.so.0
COPY --from=build /usr/lib/${ARCH}-linux-gnu/libGLX.so.0 /usr/lib/${ARCH}-linux-gnu/libGLX.so.0
COPY --from=build /usr/lib/${ARCH}-linux-gnu/libGLdispatch.so.0 /usr/lib/${ARCH}-linux-gnu/libGLdispatch.so.0
COPY --from=build /usr/lib/${ARCH}-linux-gnu/libgthread-2.0.so.0 /usr/lib/${ARCH}-linux-gnu/libgthread-2.0.so.0
COPY --from=build /usr/lib/${ARCH}-linux-gnu/libX11.so.6 /usr/lib/${ARCH}-linux-gnu/libX11.so.6
COPY --from=build /usr/lib/${ARCH}-linux-gnu/libXext.so.6 /usr/lib/${ARCH}-linux-gnu/libXext.so.6
COPY --from=build /usr/lib/${ARCH}-linux-gnu/libxcb.so.1 /usr/lib/${ARCH}-linux-gnu/libxcb.so.1
COPY --from=build /usr/lib/${ARCH}-linux-gnu/libXau.so.6 /usr/lib/${ARCH}-linux-gnu/libXau.so.6
COPY --from=build /usr/lib/${ARCH}-linux-gnu/libXdmcp.so.6 /usr/lib/${ARCH}-linux-gnu/libXdmcp.so.6
COPY --from=build /usr/lib/${ARCH}-linux-gnu/libbsd.so.0 /usr/lib/${ARCH}-linux-gnu/libbsd.so.0

# site-packagesをコピー
COPY --from=build /usr/local/lib/python3.9/site-packages /usr/lib/python3.9/dist-packages

WORKDIR /app
COPY . /app

EXPOSE 8004
ENTRYPOINT ["python", "-m", "uvicorn", "ocreniisan.main:app", "--workers", "4", "--reload", "--host", "0.0.0.0", "--port", "8004"]
