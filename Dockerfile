FROM python:3.10.17-slim

LABEL maintainer="szymon.wais@gmail.com"

ENV PYTHONUNBUFFERED=1

# Kopiowanie plików
COPY ./requirements.txt /requirements.txt
COPY ./langbuddy /langbuddy
COPY /scripts /scripts

WORKDIR /langbuddy
EXPOSE 8000

# Instalacja zależności systemowych
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev \
    gcc \
    g++ \
    build-essential \
    python3-dev \
    linux-headers-amd64 \
    && python -m venv /py \
    && /py/bin/pip install --upgrade pip \
    && /py/bin/pip install -r /requirements.txt \
    && apt-get purge -y --auto-remove gcc g++ build-essential python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --no-create-home langbuddy \
    && mkdir -p /vol/web/static /vol/web/media \
    && chmod -R 755 /vol \
    && chown -R langbuddy:langbuddy /vol \
    && chmod -R +x /scripts

RUN mkdir -p /home/langbuddy/.cache/whisper && \
    chown -R langbuddy:langbuddy /home/langbuddy

ENV PATH="/scripts:/py/bin:$PATH"

USER langbuddy

CMD ["run.sh"]
