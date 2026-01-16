import time
import uuid
import json
import base64
import logging
from pathlib import Path
from worker import redis_client
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import models
import config

logging.basicConfig(
    level=getattr(logging, config.log_level),
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
)


app = FastAPI(title="API")


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TTSRequest(BaseModel):
    params: Dict[str, Any]


class TasksResponse(BaseModel):
    total: int
    tasks: List[Dict[str, Any]]


class UpdateTaskRequest(BaseModel):
    task_id: str
    status: Optional[str] = None
    result: Optional[str] = None
    duration: Optional[float] = None
    error_msg: Optional[str] = None
    retry_time: Optional[int] = None
    task_result: Optional[Dict[str, Any]] = None


# --------------------
# Frontend served at /
# API docs at /docs
# --------------------


# --------------------
# API 接口
# --------------------


# --------------------
# IndexTTS 提交接口 (原 /tts，现在重命名为 /tts/index-tts)
# --------------------
@app.post(
    "/tts/index-tts",
    summary="Submit IndexTTS task",
    description="""
提交IndexTTS任务。`params` 参数会直接传给 `IndexTTS2.infer()`。

**可传字段示例**：

- `text`: str, 要合成的文本
- `spk_audio_prompt`: str, 参考音频路径，用于克隆说话人
- `emo_vector`: list[float], 8维情感向量 `[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]`
- `cfg_value`: float, LM引导强度
- `inference_timesteps`: int, 推理步数
- `normalize`: bool, 是否启用外部文本归一化
- `denoise`: bool, 是否启用降噪
- `retry_badcase`: bool, 是否重试坏案例
- `retry_badcase_max_times`: int, 最大重试次数
- `retry_badcase_ratio_threshold`: float, 坏案例检测长度阈值
- `use_random`: bool, 是否启用随机性
- `output_path`: str, 输出wav路径
- `verbose`: bool, 是否打印详细推理信息

**示例 JSON**：

```json
{
  "params": {
    "text": "hello",
    "spk_audio_prompt": "examples/voice_01.wav",
    "emo_vector": [0,0,0,0,0,0,0,0],
    "cfg_value": 2,
    "inference_timesteps": 10,
    "normalize": false,
    "denoise": false,
    "retry_badcase": true,
    "retry_badcase_max_times": 3,
    "retry_badcase_ratio_threshold": 6,
    "use_random": false,
    "output_path": "tasks/output.wav",
    "verbose": true
  }
}
""",
)
async def submit_index_tts(req: TTSRequest):
    logging.debug(f"Request body: {req.dict()}")
    print(f"DEBUG: Received IndexTTS request with params: {req.params}")
    task_data = req.params
    # Insert into MySQL
    task_id = models.insert_task(task_data, "index-tts")

    # Get retry_time for queue
    task_info = models.get_task(task_id)
    retry_time = task_info.get("retry_time", 3) if task_info else 3

    # Push to Redis
    queue_name = "tasks:index-tts"
    task_for_queue = {"id": task_id, "payload": task_data, "retry_time": retry_time}
    try:
        redis_client.lpush(queue_name, json.dumps(task_for_queue))
        print(f"DEBUG: Created IndexTTS task {task_id}")
        response = {"task_id": task_id}
        logging.debug(f"Response: {response}")
        return response
    except Exception as e:
        # If Redis fails, log and return error
        logging.error(f"Failed to submit task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue task")
    except Exception as e:
        # If Redis fails, optionally delete from DB
        # But for now, just log and return error
        logging.error(f"Failed to submit task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue task")


# --------------------
# VoxCPM 提交接口
# --------------------
@app.post(
    "/tts/voxcpm",
    summary="Submit VoxCPM task",
    description="""
提交VoxCPM任务。`params` 参数会直接传给 `VoxCPM.generate()`。

**可传字段示例**：

- `text`: str, 要合成的文本
- `prompt_wav_path`: str, 参考音频路径，用于克隆说话人 (对应 spk_audio_prompt)
- `prompt_text`: str, 参考音频对应文本
- `cfg_value`: float, guidance 强度（1.5~2.5 推荐）
- `inference_timesteps`: int, LocDiT 推理步数（越大越慢但更稳）
- `normalize`: bool, 是否保留原始文本（推荐 False）
- `denoise`: bool, 是否启用 16kHz 降噪（推荐 False）
- `retry_badcase`: bool, 是否启用异常自动重试
- `retry_badcase_max_times`: int, 最多重试次数
- `retry_badcase_ratio_threshold`: float, 语音过长判定阈值

**示例 JSON**：

```json
{
  "params": {
    "text": "Translate for me, what is a surprise!",
    "prompt_wav_path": "examples/voice_01.wav",
    "prompt_text": "Translate for me, what is a surprise!",
    "cfg_value": 2.0,
    "inference_timesteps": 10,
    "normalize": false,
    "denoise": false,
    "retry_badcase": true,
    "retry_badcase_max_times": 3,
    "retry_badcase_ratio_threshold": 6.0
  }
}
""",
)
async def submit_voxcpm_tts(req: TTSRequest):
    logging.debug(f"Request body: {req.dict()}")
    print(f"DEBUG: Received VoxCPM request with params: {req.params}")
    task_data = req.params
    # Insert into MySQL
    task_id = models.insert_task(task_data, "voxcpm")

    # Get retry_time for queue
    task_info = models.get_task(task_id)
    retry_time = task_info.get("retry_time", 3) if task_info else 3

    # Push to Redis
    queue_name = "tasks:voxcpm"
    task_for_queue = {"id": task_id, "payload": task_data, "retry_time": retry_time}
    try:
        redis_client.lpush(queue_name, json.dumps(task_for_queue))
        print(f"DEBUG: Created VoxCPM task {task_id}")
        response = {"task_id": task_id}
        logging.debug(f"Response: {response}")
        return response
    except Exception as e:
        # If Redis fails, log and return error
        logging.error(f"Failed to submit task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue task")


@app.get(
    "/tts/{task_id}",
    summary="Get a specific TTS task by ID",
    description="""
Get details of a specific TTS task by its ID.

**Path Parameters**:

- `task_id`: str, The unique identifier of the task (UUID).

**Response**:

A task object containing:
- `id`: str, Unique task identifier (UUID).
- `status`: str, Current task status (`pending`, `processing`, `completed`, `failed`).
- `result`: str or null, Result output (e.g., "processed" for completed tasks).
- `audio_data`: str or null, Base64-encoded audio data with data URI prefix (only present if status is `completed` and audio file exists).
- `worker_id`: str or null, ID of the worker processing the task.
- `submit_time`: float, Timestamp when the task was submitted (from created_at).
- `start_time`: float or null, Timestamp when processing started (not directly tracked).
- `end_time`: float or null, Timestamp when processing ended (from updated_at).
- `duration`: float or null, Processing time in seconds.
- `params`: dict, TTS parameters used for the task.
- `error_msg`: str or null, Error message (only present if status is `failed`).
- `retry_time`: int, Remaining retry attempts (default 3).
- `task_result`: dict or null, Result data from processing.
- `task_type`: str or null, Type of the task (e.g., "index-tts", "voxcpm").

**Example Response** (status: completed):

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "result": "processed",
  "task_result": {"output": "processed", "duration": 1.23},
  "worker_id": "worker-uuid",
  "submit_time": 1700000000.0,
  "duration": 1.23,
  "params": {"text": "Hello"},
  "task_type": "index-tts"
}
```
""",
)
def get_task(task_id: str):
    logging.debug(f"Query params: task_id={task_id}")
    task = models.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    params = json.loads(task["data"])
    task_data = {
        "id": task["id"],
        "task_type": task["task_type"],
        "params": params,
        "status": task["status"],
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
        "duration": task["duration"],
        "error_msg": task["error_msg"],
        "retry_time": task["retry_time"],
        "task_result": json.loads(task["task_result"]) if task["task_result"] else None,
    }

    if task_data.get("status") == "completed" and task_data.get("task_result"):
        result_path = task_data["task_result"].get("output")
        if result_path:
            audio_path = Path(result_path)
            if audio_path.exists():
                with open(audio_path, "rb") as f:
                    audio_bytes = f.read()
                audio_data = f"data:audio/wav;base64,{base64.b64encode(audio_bytes).decode('utf-8')}"
                task_data["audio_data"] = audio_data
    logging.debug(f"Response: {task_data}")
    return task_data


@app.get(
    "/tasks",
    response_model=TasksResponse,
    summary="Get TTS tasks filtered by status",
    description="""
Get a list of TTS tasks filtered by their status.

**Query Parameters**:

- `status`: str, Filter tasks by status. Options: `pending`, `processing`, `completed`, `failed`. Default: `completed`.

**Response**:

- `total`: int, Total number of tasks matching the filter.
- `tasks`: list, Array of task objects. Each task object contains:
  - `id`: str, Unique task identifier (UUID).
  - `status`: str, Current task status (`pending`, `processing`, `completed`, `failed`).
  - `result`: str or null, Result output extracted from `task_result["output"]`.
  - `worker_id`: str or null, ID of the worker processing the task.
  - `submit_time`: float, Timestamp when the task was submitted (from created_at).
  - `start_time`: float or null, Timestamp when processing started (not directly tracked).
  - `end_time`: float or null, Timestamp when processing ended (from updated_at).
  - `duration`: float or null, Processing time in seconds.
  - `params`: dict, TTS parameters used for the task.
  - `error_msg`: str or null, Error message (only present if status is `failed`).
  - `retry_time`: int, Remaining retry attempts.
  - `task_result`: dict or null, Result data from processing (e.g., {"output": "processed", "duration": 1.23}).
  - `task_type`: str or null, Type of the task (e.g., "index-tts", "voxcpm").

**Example Response**:

```json
{
  "total": 2,
  "tasks": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "completed",
      "result": "processed",
      "task_result": {"output": "processed", "duration": 1.23},
      "submit_time": 1700000000.0,
      "duration": 1.23,
      "params": {"text": "Hello"},
      "task_type": "index-tts"
    }
  ]
}
```
""",
)
def get_all_tasks(
    status: str = Query(
        "completed",
        description="Filter tasks by status: pending, processing, completed, failed",
    ),
):
    """Get list of TTS tasks filtered by status."""
    logging.debug(f"Query params: status={status}")
    rows = models.get_tasks_by_status(status)

    tasks = []
    for row in rows:
        params = json.loads(row["data"])
        task_data = {
            "id": row["id"],
            "task_type": row["task_type"],
            "params": params,
            "status": row["status"],
            "result": (
                json.loads(row["task_result"]) if row["task_result"] else {}
            ).get("output"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "duration": row["duration"],
            "error_msg": row["error_msg"],
            "retry_time": row["retry_time"],
            "task_result": json.loads(row["task_result"])
            if row["task_result"]
            else None,
        }
        tasks.append(task_data)

    response = TasksResponse(total=len(tasks), tasks=tasks)
    logging.debug(f"Response: {response.dict()}")
    return response


@app.post("/update_task")
async def update_task(req: UpdateTaskRequest):
    logging.debug(f"Request body: {req.dict()}")
    kwargs = {}
    if req.status:
        kwargs["status"] = req.status
    if req.duration is not None:
        kwargs["duration"] = req.duration
    if req.error_msg:
        kwargs["error_msg"] = req.error_msg
    if req.retry_time is not None:
        kwargs["retry_time"] = req.retry_time
    if req.task_result:
        kwargs["task_result"] = json.dumps(req.task_result)
    models.update_task(req.task_id, **kwargs)
    response = {"message": "Task updated"}
    logging.debug(f"Response: {response}")
    return response


@app.get("/queue/length")
async def get_queue_length(task_type: Optional[str] = None):
    logging.debug(f"Query params: task_type={task_type}")
    if task_type:
        queue_name = f"tasks:{task_type}"
        length = redis_client.llen(queue_name)
        response = {f"queue_length_{task_type}": length}
    else:
        lengths = {}
        for t in ["index-tts", "voxcpm"]:
            queue_name = f"tasks:{t}"
            lengths[f"queue_length_{t}"] = redis_client.llen(queue_name)
        response = lengths
    logging.debug(f"Response: {response}")
    return response


# --------------------
# __main__ 入口
# --------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",  # 注意这里用字符串：模块名:app
        host="0.0.0.0",
        port=8989,
        reload=True,  # 开启自动重载
    )
