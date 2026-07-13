# algoflow-algo-provider-example

这是算法提供方按新版 node-agent 协议接入的最小示例。只提供普通 HTTP 算法服务。

## 算法接口

代码在：

```text
provider_example/server.py
```

启动后打印：

```text
ALGO_READY
```

提供：

```text
POST /execute
```

请求：

```json
{
  "task_id": "task-xxx",
  "params": {
    "name": "张三"
  },
  "config": {
    "domain": "static.example.com",
    "object": {
      "bucketName": "example-bucket",
      "accessKeyId": "<access-key-id>",
      "accessKeySecret": "<access-key-secret>",
      "endpoint": "https://example-bucket.cos.ap-shanghai.myqcloud.com"
    }
  }
}
```

响应：

```json
{
  "status": "success",
  "result": {
    "task_id": "task-xxx",
    "name": "张三",
    "message": "张三成功",
    "delay_seconds": 12.345
  }
}
```

## 本地运行算法服务

只跑算法服务：

```bash
cd /Users/xy/algoflow-task/algoflow-algo-provider-example
python -m provider_example.server
```

默认监听 `8080`。如果本地 `8080` 已被占用，可以指定 `ALGO_PORT`：

```bash
ALGO_PORT=19002 python -m provider_example.server
```

手动调用：

```bash
curl -X POST http://127.0.0.1:8080/execute \
  -H 'Content-Type: application/json' \
  -d '{"task_id":"task-local","params":{"name":"张三"}}'
```

如果指定了 `ALGO_PORT=19002`，调用地址改成：

```bash
curl -X POST http://127.0.0.1:19002/execute \
  -H 'Content-Type: application/json' \
  -d '{"task_id":"task-local","params":{"name":"张三"}}'
```

## 通过 node-agent 运行

先启动 scheduler，再启动 node-agent 包住算法服务：

```bash
cd /Users/xy/algoflow-task

NODE_TYPE=video_translate \
SCHEDULER_URL=http://127.0.0.1:8010 \
ALGO_CMD="cd /Users/xy/algoflow-task/algoflow-algo-provider-example && python -m provider_example.server" \
ALGO_PORT=19002 \
go run ./algoflow-task-node/cmd/node-agent
```

scheduler 的队列动作要配置成：

```json
{"action":"ASSIGN","api":"/assign"}
```

scheduler 会向 node-agent 下发：

```json
{
  "task_id": "task-xxx",
  "params": {
    "name": "张三"
  }
}
```

## 镜像

provider 镜像里会从 `algoflow-task-node:v0.1.8` 拷贝 Go node-agent，然后启动本项目的算法服务。

构建前先推 node-agent 镜像：

```bash
cd /Users/xy/algoflow-task
algoflow-task-node/build_push.sh
```

再推 example：

```bash
algoflow-algo-provider-example/build_push.sh
```
