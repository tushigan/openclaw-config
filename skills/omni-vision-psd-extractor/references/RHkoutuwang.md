---
name: rh-matting-integration (RH抠图王服务接入机制)
description: RH抠图王 (RunningHub Matting) 服务接入机制与API调用文档。用于其他 AI 智能体了解并直接接入此透明背景抠图服务。
---

# RH抠图王 (RunningHub Matting) 接入指南

本技能文档详细记录了 N8N 系统中“RH抠图王”的工作机制及 API 接入方式。
RH抠图王能够将带有纯色背景（或绿幕）的图片，进行高精度前景剥离，最终生成保留 Alpha 通道的透明背景 PNG 图片。
任何 AI Agent 或前端系统如果需要接入该抠图服务，均需遵循本指南所定义的请求结构与轮询机制。

## 🔐 鉴权信息 (Authentication)

调用此服务必须使用指定的 API Key。**注意：系统已强制要求使用以下指定的 Key**：
- **API Key**: `442de49dcb5247a285b678a4c70e7499`

请求头必须携带：
```http
Authorization: Bearer 442de49dcb5247a285b678a4c70e7499
Content-Type: application/json
```

---

## 🛠️ 核心机制 (Mechanism)

RH抠图王的底层基于异步执行机制，工作流如下：
1. **创建任务 (Create Task)**：发送待抠图的图片 URL 给后端，获取一个异步 `taskId`。
2. **轮询状态 (Polling Status)**：使用获取到的 `taskId` 持续查询任务进度，直至状态返回 `SUCCESS` 或 `FAILED`。
3. **获取结果 (Fetch Result)**：任务成功后，提取返回结果中的透明 PNG 图片 URL 并下载。

### 📌 节点说明
该接口内部使用的是指定的 RunningHub ComfyUI 工作流。关键参数如下：
- `webappId`: 默认传 `2064637853572878337` (系统内部绑定的应用ID)
- `nodeId`: 图像输入节点默认绑定为 `"151"` (从URL加载节点)
- `fieldName`: `"url"`

---

## 🚀 API 调用流程 (API Flow)

### 步骤 1：提交抠图任务

- **Endpoint**: `POST https://www.runninghub.cn/task/openapi/ai-app/run`
- **Headers**: 见上文
- **Body (JSON)**:

```json
{
  "apiKey": "442de49dcb5247a285b678a4c70e7499",
  "webappId": 2064637853572878337,
  "nodeInfoList": [
    {
      "nodeId": "151",
      "fieldName": "url",
      "fieldValue": "【你要进行抠图的图片公共URL】"
    }
  ]
}
```

- **响应处理**:
  - 请求成功后，提取 `data.taskId`。
  - 若 `code` 不等于 `0`，则代表任务创建失败，应抛出 `msg` 错误信息。

### 步骤 2：轮询任务进度

任务创建成功后，需每隔 **3秒** 进行一次状态轮询。最大超时时间建议设定为 **120秒**。

- **Endpoint**: `POST https://www.runninghub.cn/openapi/v2/query`
- **Headers**: 见上文
- **Body (JSON)**:

```json
{
  "taskId": "【第一步获取的 taskId】"
}
```

- **响应状态处理**:
  - `status == "SUCCESS"`：任务完成。此时应提取 `results` 数组中第一项的 `url`。该 URL 即为抠图后的带 Alpha 通道的**透明PNG图片**。
  - `status == "FAILED"`：任务失败。提取并记录 `errorCode` 和 `errorMessage` 以供排查。
  - 其他状态（如 `PENDING`，`RUNNING`）：继续等待，`sleep(3)` 后再次请求。

### 步骤 3：下载最终结果图片

获取到 `result_url` 后，直接发送标准 HTTP/HTTPS GET 请求将其下载。
- **注意**：下载可能会失败，应当检查 HTTP 响应状态码 (`status_code == 200`)。

---

## 💻 Python 代码示例

如果你正在编写后端整合脚本，可以参考以下异步请求逻辑：

```python
import httpx
import asyncio

async def run_rh_matting(image_url: str) -> bytes:
    api_key = "442de49dcb5247a285b678a4c70e7499"
    webapp_id = 2064637853572878337
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 1. 提交任务
    run_url = "https://www.runninghub.cn/task/openapi/ai-app/run"
    payload = {
        "apiKey": api_key,
        "webappId": webapp_id,
        "nodeInfoList": [
            {"nodeId": "151", "fieldName": "url", "fieldValue": image_url}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(run_url, headers=headers, json=payload, timeout=60)
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"RH抠图王任务创建失败: {data.get('msg')}")
            
        task_id = str(data["data"]["taskId"])
        print(f"[RH抠图王] 任务创建成功，taskId: {task_id}，开始轮询...")
        
        # 2. 轮询状态
        query_url = "https://www.runninghub.cn/openapi/v2/query"
        for _ in range(40): # 最大 120 秒
            await asyncio.sleep(3)
            q_resp = await client.post(query_url, headers=headers, json={"taskId": task_id}, timeout=30)
            q_data = q_resp.json()
            status = q_data.get("status")
            
            if status == "SUCCESS":
                results = q_data.get("results", [])
                if results:
                    result_url = results[0].get("url")
                    print(f"[RH抠图王] 抠图完成，下载透明PNG: {result_url}")
                    
                    # 3. 下载图片二进制流
                    img_resp = await client.get(result_url, timeout=30)
                    if img_resp.status_code == 200:
                        return img_resp.content
                    else:
                        raise Exception(f"图片下载失败 HTTP {img_resp.status_code}")
                raise Exception("任务成功但无结果图片")
            elif status == "FAILED":
                raise Exception(f"RH抠图王任务失败: {q_data.get('errorMessage')}")
                
        raise Exception("RH抠图王等待超时")
```
