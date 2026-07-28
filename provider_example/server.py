from __future__ import annotations

import json
import hashlib
import math
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


DEFAULT_DELAY_MIN_SECONDS = 23.0
DEFAULT_DELAY_MAX_SECONDS = 40.0
TASK_BEHAVIORS = {"success", "fail_once", "fail_always"}
_attempt_lock = threading.Lock()
_failed_once_tasks: set[str] = set()


class Handler(BaseHTTPRequestHandler):
    delay_min_seconds = DEFAULT_DELAY_MIN_SECONDS
    delay_max_seconds = DEFAULT_DELAY_MAX_SECONDS
    attempt_state_dir = ""

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
            delay_seconds = _task_delay_seconds(
                params, self.delay_min_seconds, self.delay_max_seconds
            )
            behavior = _task_behavior(params)
            config_domain = config.get("domain", "")
            print(
                f"收到任务 task_id={task_id} name={name} config_domain={config_domain} "
                f"behavior={behavior} delay_seconds={delay_seconds:.3f}",
                flush=True,
            )
            time.sleep(delay_seconds)
            if _should_fail_task(task_id, behavior, self.attempt_state_dir):
                self._write_json(
                    200,
                    {
                        "status": "failed",
                        "error": f"simulated {behavior} failure",
                        "result": {
                            "task_id": task_id,
                            "name": name,
                            "behavior": behavior,
                            "delay_seconds": round(delay_seconds, 3),
                        },
                    },
                )
                return
            self._write_json(
                200,
                {
                    "status": "success",
                    "result": {
                        "task_id": task_id,
                        "name": name,
                        "message": f"{name}成功",
                        "behavior": behavior,
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


def _task_delay_seconds(
    params: dict[str, Any], minimum: float, maximum: float
) -> float:
    value = params.get("delay_seconds")
    if value is None:
        return random.uniform(minimum, maximum)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("delay_seconds must be a non-negative number")
    delay = float(value)
    if not math.isfinite(delay) or delay < 0:
        raise ValueError("delay_seconds must be a non-negative number")
    return delay


def _task_behavior(params: dict[str, Any]) -> str:
    value = params.get("behavior", "success")
    if not isinstance(value, str) or value not in TASK_BEHAVIORS:
        raise ValueError("behavior must be success, fail_once, or fail_always")
    return value


def _should_fail_task(task_id: str, behavior: str, state_dir: str) -> bool:
    if behavior == "success":
        return False
    if behavior == "fail_always":
        return True
    if behavior != "fail_once":
        raise ValueError("unsupported task behavior")

    if state_dir:
        os.makedirs(state_dir, exist_ok=True)
        marker = os.path.join(
            state_dir, hashlib.sha256(task_id.encode("utf-8")).hexdigest()
        )
        try:
            descriptor = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            return False
        else:
            os.close(descriptor)
            return True

    with _attempt_lock:
        if task_id in _failed_once_tasks:
            return False
        _failed_once_tasks.add(task_id)
        return True


def _delay_range_seconds() -> tuple[float, float]:
    minimum = _nonnegative_float_env(
        "PROVIDER_DELAY_MIN_SECONDS", DEFAULT_DELAY_MIN_SECONDS
    )
    maximum = _nonnegative_float_env(
        "PROVIDER_DELAY_MAX_SECONDS", DEFAULT_DELAY_MAX_SECONDS
    )
    if maximum < minimum:
        raise ValueError(
            "PROVIDER_DELAY_MAX_SECONDS must be greater than or equal to "
            "PROVIDER_DELAY_MIN_SECONDS"
        )
    return minimum, maximum


def _nonnegative_float_env(key: str, default: float) -> float:
    raw = os.environ.get(key)
    if raw is None or not raw.strip():
        return default
    value = float(raw)
    if value < 0:
        raise ValueError(f"{key} must be non-negative")
    return value


def main() -> None:
    port = int(os.environ.get("ALGO_PORT", "8080"))
    Handler.delay_min_seconds, Handler.delay_max_seconds = _delay_range_seconds()
    Handler.attempt_state_dir = os.environ.get("PROVIDER_ATTEMPT_STATE_DIR", "").strip()
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print("ALGO_READY", flush=True)  # 算法节点准备好，可以接收任务了
    server.serve_forever()


if __name__ == "__main__":
    main()
