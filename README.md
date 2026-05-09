# algoflow-algo-provider-example

这是一个算法提供方接入 `algoflow-task-node` 的独立示例项目。

重点：

- 这个项目不属于框架。
- 算法方只实现自己的 `Algorithm` 类。
- 注册、下线、HTTP 服务、callback 都由 `algoflow-task-node` 框架处理。
- 一个 Pod 同一时刻只处理一个 task；要并发处理就扩 Pod 副本数。

## 1. 项目结构

```text
algoflow-algo-provider-example/
  pyproject.toml
  provider_example/
    __init__.py
    simple_name_algorithm.py
  sample_payload.json
  Dockerfile
  deployment.yaml
```

## 2. 本地启动

先启动 scheduler，然后启动这个算法节点：

```bash
cd /Users/xy/algoflow-task/algoflow-algo-provider-example

QUEUE_NAME=video_translate \
SCHEDULER_URL=http://127.0.0.1:8010 \
uv run algoflow-node --algorithm provider_example.simple_name_algorithm:NameSuccessAlgorithm
```

`NODE_NAME`、`NODE_URL` 不写时由框架自动探测；本地要同时启动多个节点时，再手动覆盖 `PORT`、`NODE_NAME`、`NODE_URL`。

健康检查：

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/readyz
```

## 3. 提交任务 payload

gateway 提交任务时，`payload` 示例：

```json
{
  "name": "张三"
}
```

这个 payload 会原样进入：

```python
NameSuccessAlgorithm.handle_task(payload, context)
```

算法会：

1. 从 `payload.name` 读取名字。
2. 随机等待 10 到 15 秒。
3. 返回 `{name}成功`。

回调结果里的 `data` 类似：

```json
{
  "task_id": "task-xxx",
  "name": "张三",
  "message": "张三成功",
  "delay_seconds": 12.345
}
```

## 4. 算法方需要实现什么

核心代码在：

```text
provider_example/simple_name_algorithm.py
```

必须继承：

```python
from algoflow_task_node import AlgoflowAlgorithm
```

必须实现：

```python
async def handle_task(self, payload, context):
    ...
```

`handle_task` 在同一个 node 进程内不会并发执行。算法代码里可以按单任务处理模型写本地临时文件、模型上下文和外部 job 状态；如果要提高吞吐，增加 Deployment replicas。

可选实现：

```python
async def startup(self, context):
    ...

async def env_init(self, payload, context):
    ...

async def shutdown(self, context):
    ...
```

## 5. K8s 接入

`deployment.yaml` 里已经演示：

- `preStop` 调 `/shutdown`。
- `readinessProbe` 走 `/readyz`。
- `livenessProbe` 走 `/healthz`。
- Pod name、Pod IP、node name、node url 由框架自动探测。

正常滚动更新、缩容、删除 Pod 时，框架会主动从 scheduler 下线。

## 6. Docker 构建

发布算法包到内部源：

```bash
cd /Users/xy/algoflow-task/algoflow-algo-provider-example
./publish.sh
```

先发布框架包：

```bash
cd /Users/xy/algoflow-task/algoflow-task-node
./publish.sh
```

算法项目依赖的是内部源里的框架包：

```toml
dependencies = [
    "algoflow-task-node==0.1.1",
]
```

镜像名默认使用项目目录名，镜像版本从 `pyproject.toml` 读取：

```text
name = "algoflow-algo-provider-example"
version = "0.1.0"
```

打包并推送：

```bash
cd /Users/xy/algoflow-task
algoflow-algo-provider-example/build_push.sh
```

当前会推送到：

```text
hx-repo.tencentcloudcr.com/engine/algoflow-algo-provider-example:0.1.0
```

以后要改镜像版本，直接改 `pyproject.toml` 里的 `version`。
