FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bodega ./bodega

# Usuario sin privilegios; /data guarda el CSV (volumen montado desde el host)
RUN useradd --create-home --uid 1000 app && mkdir -p /data && chown app /data
USER app

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn", "--factory", "bodega.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
