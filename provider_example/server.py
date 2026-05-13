from __future__ import annotations

import json
import os
import random
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class Handler(BaseHTTPRequestHandler):
    # 健康检查
    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._write_json(200, {"status": "ok"})
            return
        self._write_json(404, {"error": "not found"})

    # 执行任务
    def do_POST(self) -> None:
        if self.path != "/execute":
            self._write_json(404, {"error": "not found"})
            return
        try:
            request = self._read_json()
            task_id = _required_string(request, "task_id")

            # 获取 params 具体透传的参数
            params = request.get("params")
            if not isinstance(params, dict):
                raise ValueError("params is required")

            # 获取 config，如果算法有需要可以使用
            config = request.get("config") or {}
            if not isinstance(config, dict):
                raise ValueError("config must be an object")

            name = _required_string(params, "name")  # 直接获取 name 参数
            delay_seconds = random.uniform(10, 15)
            config_domain = config.get("domain", "")
            print(
                f"收到任务 task_id={task_id} name={name} config_domain={config_domain} delay_seconds={delay_seconds:.3f}",
                flush=True,
            )
            time.sleep(delay_seconds)
            self._write_json(
                200,
                {
                    "status": "success",
                    "result": {
                        "task_id": task_id,
                        "name": name,
                        "message": f"{name}成功",
                        "delay_seconds": round(delay_seconds, 3),
                    },
                },
            )
        except Exception as exc:
            self._write_json(200, {"status": "failed", "error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        print(format % args, flush=True)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(length) if length > 0 else b"{}"
        value = json.loads(data.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("body must be an object")
        return value

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} is required")
    return value


def main() -> None:
    port = int(os.environ.get("ALGO_PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print("ALGO_READY", flush=True)  # 算法节点准备好，可以接收任务了
    server.serve_forever()


if __name__ == "__main__":
    main()
