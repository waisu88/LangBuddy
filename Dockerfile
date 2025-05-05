FROM python:3.10.17-slim

LABEL maintainer="szymon.wais@gmail.com"

ENV PYTHONUNBUFFERED=1
ENV PATH="/scripts:/py/bin:$PATH"
ENV XDG_CACHE_HOME="/tmp"

# Kopiowanie plików
COPY ./requirements.txt /requirements.txt
COPY ./langbuddy /langbuddy
COPY /scripts /scripts

WORKDIR /langbuddy
EXPOSE 8000

# Instalacja zależności systemowych i Pythona
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
    # ⬇️ Instalacja torch jako binarka z oficjalnego źródła (CPU)
    && /py/bin/pip install --only-binary=:all: --prefer-binary torch --index-url https://download.pytorch.org/whl/cpu \
    # ⬇️ Instalacja pozostałych zależności
    && /py/bin/pip install --no-cache-dir -r /requirements.txt \
    # ⬇️ Sprzątanie
    && apt-get purge -y --auto-remove gcc g++ build-essential python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Dodanie użytkownika aplikacyjnego
RUN useradd --system --no-create-home langbuddy \
    && mkdir -p /vol/web/static /vol/web/media \
    && chmod -R 755 /vol \
    && chown -R langbuddy:langbuddy /vol \
    && chmod -R +x /scripts

    
USER langbuddy


CMD ["run.sh"]

