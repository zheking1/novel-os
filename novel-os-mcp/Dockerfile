ARG PYTHON_IMAGE=docker.1ms.run/library/python:3.12-slim
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

WORKDIR /app

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --default-timeout=300 --retries 10 hatchling && \
    mkdir -p src/novel_os_mcp && \
    printf "__version__ = '0.1.0'\n" > src/novel_os_mcp/__init__.py && \
    pip install --no-cache-dir --default-timeout=300 --retries 10 -e .

COPY src ./src

EXPOSE 8787

CMD ["novel-os-mcp"]
