FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir uv \
    && export UV_INSECURE_HOST=172.20.162.20 \
    && uv sync

EXPOSE 8000

CMD ["uv", "run", "algoflow-node", "--algorithm", "provider_example.simple_name_algorithm:NameSuccessAlgorithm"]
