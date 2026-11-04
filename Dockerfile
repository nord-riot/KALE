FROM python:3.12-alpine
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 KALE_HOST=0.0.0.0 KALE_PORT=8080
WORKDIR /app
COPY server.py /app/
COPY web/ /app/web/
COPY data/ /app/data/
RUN addgroup -S kale && adduser -S -G kale kale && chown -R kale:kale /app
USER kale
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health',timeout=2).read()" || exit 1
CMD ["python", "/app/server.py"]
