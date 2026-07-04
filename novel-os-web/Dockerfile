FROM docker.1ms.run/library/python:3.12-slim

WORKDIR /app

# Install PostgreSQL client library, psycopg2, and bcrypt
RUN apt-get update && apt-get install -y libpq-dev gcc && \
    pip install --no-cache-dir psycopg2-binary bcrypt && \
    apt-get remove -y gcc && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

COPY server.py index.html spa.html /app/
COPY js/ /app/js/
COPY css/ /app/css/

ENV NOVEL_OS_WEB_HOST=0.0.0.0
ENV NOVEL_OS_WEB_ROOT=/app
ENV NOVEL_OS_WEB_PORT=8790
ENV NOVEL_OS_MCP_URL=http://novel-os-mcp:8787/mcp
ENV NOVEL_OS_WEB_DATA_DIR=/app/data

EXPOSE 8790

CMD ["python", "server.py"]
