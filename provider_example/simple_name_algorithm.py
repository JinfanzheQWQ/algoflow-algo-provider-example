from __future__ import annotations

import asyncio
import random
from typing import Any

from algoflow_task_node import AlgoflowAlgorithm, NodeContext, TaskContext


class NameSuccessAlgorithm(AlgoflowAlgorithm):
    """最简单的算法接入示例：从 payload 读取 name，等待 10-15 秒后返回成功。"""

    async def startup(self, context: NodeContext) -> None:
        print(f"node started name={context.node_name} queue={context.queue_name}")

    async def env_init(self, payload: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        return {"ok": True, "node": context.node_name}

    async def handle_task(self, payload: dict[str, Any], context: TaskContext) -> dict[str, Any]:
        name = _required_string(payload, "name")
        delay_seconds = random.uniform(10, 15)
        print(
            f"收到任务 task_id={context.task_id} name={name} delay_seconds={delay_seconds:.3f}",
            flush=True,
        )
        await asyncio.sleep(delay_seconds)
        return {
            "task_id": context.task_id,
            "name": name,
            "message": f"{name}成功",
            "delay_seconds": round(delay_seconds, 3),
        }

    async def shutdown(self, context: NodeContext) -> None:
        print(f"node shutdown name={context.node_name}")


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"payload.{key} is required")
    return value
