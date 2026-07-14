FROM python:3.12-slim

LABEL org.opencontainers.image.title="authentik-enum" \
      org.opencontainers.image.description="Identify Authentik versions by fingerprinting publicly-served static assets" \
      org.opencontainers.image.source="https://github.com/l4rm4nd/Authentik-Enum"

WORKDIR /app

COPY authentik-enum.py ./

RUN useradd -r -s /bin/false appuser
USER appuser

ENTRYPOINT ["python3", "authentik-enum.py"]
