#!/usr/bin/env bash
set -euo pipefail

# 镜像版本从 pyproject.toml 读取，镜像名默认使用项目目录名。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TENCENT_REGISTRY="hx-repo.tencentcloudcr.com/engine"
PLATFORM="linux/amd64"
IMAGE_NAME="$(basename "$SCRIPT_DIR")"
UV_CACHE_DIR="${UV_CACHE_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)/.uv-cache}"
export UV_CACHE_DIR

PROJECT_VERSION="$(uv version --directory "$SCRIPT_DIR" --short)"
IMAGE="${TENCENT_REGISTRY}/${IMAGE_NAME}:${PROJECT_VERSION}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker command not found" >&2
  exit 1
fi

echo "building image: ${IMAGE}"
echo "platform: ${PLATFORM}"
docker build --platform "$PLATFORM" -t "$IMAGE" "$SCRIPT_DIR"

echo "pushing image: ${IMAGE}"
docker push "$IMAGE"

echo "done: ${IMAGE}"
