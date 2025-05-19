FROM python:3.10.17-slim

LABEL maintainer="szymon.wais@gmail.com"

ENV PYTHONUNBUFFERED=1
ENV PATH="/scripts:/py/bin:$PATH"

ENV XDG_CACHE_HOME="/app/whisper"

# --- WSTĘPNA KONFIGURACJA I INSTALACJE ---

# Skopiuj tylko requirements (rzadko się zmienia)
COPY ./requirements.txt /requirements.txt

# Instalacja systemowych i Pythona (ta warstwa będzie cache'owana)
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
 && /py/bin/pip install --only-binary=:all: --prefer-binary torch --index-url https://download.pytorch.org/whl/cpu \
 && /py/bin/pip install --no-cache-dir -r /requirements.txt \
 && apt-get purge -y --auto-remove gcc g++ build-essential python3-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Dodanie użytkownika aplikacyjnego
RUN useradd --system --no-create-home langbuddy \
 && mkdir -p /vol/web/static /vol/web/media \
 && chmod -R 755 /vol


# --- DOPIERO TERAZ kopiuj kod i skrypty (które się zmieniają) ---
COPY ./langbuddy /langbuddy
COPY /scripts /scripts

RUN chown -R langbuddy:langbuddy /vol /langbuddy /scripts \
 && chmod -R +x /scripts

USER langbuddy


WORKDIR /langbuddy
EXPOSE 8000

CMD ["/scripts/run.sh"]