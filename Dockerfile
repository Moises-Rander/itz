# Backend Django para o Google Cloud Run (escala a zero; cold start curto).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Arquivos estáticos do Admin, servidos pelo WhiteNoise. A chave aqui é só
# para o comando rodar no build; a de produção vem das variáveis do serviço.
RUN SECRET_KEY=build-only DEBUG=False python manage.py collectstatic --noinput

# Usuário sem privilégios.
RUN useradd --create-home app && chown -R app /app
USER app

# 1 processo com várias threads: o recomendado para 1 vCPU no Cloud Run.
# --timeout 0: quem limita a duração da requisição é o próprio Cloud Run.
CMD exec gunicorn config.wsgi:application --bind :$PORT --workers 1 --threads 8 --timeout 0
