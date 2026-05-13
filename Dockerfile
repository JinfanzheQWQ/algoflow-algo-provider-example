FROM python:3.11-slim

WORKDIR /app

COPY . /app
COPY --from=hx-repo.tencentcloudcr.com/engine/algoflow-task-node:v0.1.0 /app/algoflow-task-node /usr/local/bin/algoflow-task-node

EXPOSE 8000

ENV ALGO_CMD="python -m provider_example.server"
ENV ALGO_PORT=8080

CMD ["algoflow-task-node"]
