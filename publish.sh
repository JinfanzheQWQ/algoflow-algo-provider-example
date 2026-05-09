#!/usr/bin/env bash
set -euo pipefail

# 发布算法示例包到内部 Python 源。版本号只维护 pyproject.toml 里的 project.version。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

UV_CACHE_DIR="${UV_CACHE_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)/.uv-cache}"
export UV_CACHE_DIR

echo "building algoflow-algo-provider-example..."
uv build

echo "publishing algoflow-algo-provider-example to hx..."
uv publish --index hx --username '' --password ''

echo "done"
