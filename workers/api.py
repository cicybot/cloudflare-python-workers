import json
import base64
import logging
import os
from pathlib import Path
import redis
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import models
import config

logging.basicConfig(
    level=getattr(logging, config.log_level),
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
)

# Redis client
redis_client = redis.from_url(config.redis_url, decode_responses=True)

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
    params: Dict[str, Any] = Field(
        description="Parameters for TTS inference, passed directly to the TTS model."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "params": {"text": "Hello, world!", "voice": "en-US-1", "speed": 1.0}
            }
        }
    )


class TasksResponse(BaseModel):
    total: int
    tasks: List[Dict[str, Any]]


class WorkerModel(BaseModel):
    id: str = Field(..., description="Unique identifier for the worker")
    platform: str = Field(..., description="Operating system and platform information")
    memory_total: int = Field(..., description="Total memory in bytes")
    memory_available: int = Field(..., description="Available memory in bytes")
    cpu_count: int = Field(..., description="Number of CPU cores")
    cpu_freq: float = Field(..., description="CPU frequency in MHz")
    gpu_info: Optional[str] = Field(None, description="GPU information if available")
    start_time: Optional[datetime] = Field(
        None, description="Worker registration timestamp"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "worker-123",
                "platform": "Linux-5.4.0-x86_64-with-glibc2.29",
                "memory_total": 8589934592,
                "memory_available": 4294967296,
                "cpu_count": 4,
                "cpu_freq": 2200.0,
                "gpu_info": "NVIDIA GeForce GTX 1060",
                "start_time": None,
                "updated_at": None,
            }
        }
    )


class WorkersResponse(BaseModel):
    workers: List[WorkerModel]


class UpdateTaskRequest(BaseModel):
    task_id: str
    status: Optional[str] = None
    result: Optional[str] = None
    duration: Optional[float] = None
    error_msg: Optional[str] = None
    retry_time: Optional[int] = None
    task_result: Optional[Dict[str, Any]] = None


class RegisterWorkerRequest(BaseModel):
    worker_id: str = Field(..., description="Unique identifier for the worker instance")
    platform: str = Field(..., description="Operating system and platform details")
    memory_total: int = Field(..., description="Total system memory in bytes")
    memory_available: int = Field(
        ..., description="Currently available memory in bytes"
    )
    cpu_count: int = Field(..., description="Number of CPU cores available")
    cpu_freq: float = Field(..., description="CPU clock frequency in MHz")
    gpu_info: Optional[str] = Field(
        None, description="GPU hardware information, if available"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "worker_id": "worker-001",
                "platform": "Linux-5.4.0-x86_64-with-glibc2.29",
                "memory_total": 8589934592,
                "memory_available": 4294967296,
                "cpu_count": 4,
                "cpu_freq": 2200.0,
                "gpu_info": "NVIDIA GeForce GTX 1060",
            }
        }
    )


class UpdateWorkerRequest(BaseModel):
    worker_id: str
    memory_available: Optional[int] = None
    # Add other fields if needed


class WhisperRequest(BaseModel):
    url: str


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
    "/api/tts/index-tts",
    tags=["TTS"],
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
    queue_name = "tasks:tts"
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
    "/api/tts/voxcpm",
    tags=["TTS"],
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
    queue_name = "tasks:tts"
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
    "/api/tts/{task_id}",
    tags=["Tasks"],
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
    "/api/tasks",
    tags=["Tasks"],
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


@app.post("/api/update_task", tags=["Internal"])
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


@app.post(
    "/api/register_worker",
    tags=["Internal"],
    summary="Register or update a worker",
    description="Registers a new worker or updates an existing one with system information including platform, memory, CPU, and GPU details.",
)
async def register_worker(req: RegisterWorkerRequest):
    logging.debug(f"Request body: {req.dict()}")
    try:
        models.insert_worker(
            req.worker_id,
            req.platform,
            req.memory_total,
            req.memory_available,
            req.cpu_count,
            req.cpu_freq,
            req.gpu_info,
        )
        response = {"message": "Worker registered or updated"}
    except Exception as e:
        logging.error(f"Error registering worker: {e}")
        raise HTTPException(status_code=500, detail="Failed to register worker")
    logging.debug(f"Response: {response}")
    return response


@app.post(
    "/api/update_worker",
    tags=["Internal"],
    summary="Update worker heartbeat",
    description="Updates a worker's available memory information for heartbeat monitoring.",
)
async def update_worker(req: UpdateWorkerRequest):
    logging.debug(f"Request body: {req.dict()}")
    kwargs = {}
    if req.memory_available is not None:
        kwargs["memory_available"] = req.memory_available
    models.update_worker(req.worker_id, **kwargs)
    response = {"message": "Worker updated"}
    logging.debug(f"Response: {response}")
    return response


@app.get(
    "/api/workers",
    tags=["Internal"],
    summary="Get all registered workers",
    description="Returns a list of all workers currently registered in the system, including their platform, memory, CPU, and GPU information.",
    response_model=WorkersResponse,
)
async def get_workers():
    workers = models.get_all_workers()
    return {"workers": workers}


@app.post(
    "/api/upload",
    tags=["Files"],
    summary="Upload a file",
    description="""
Upload a file to the media directory.

- **file**: The file to upload (binary data).
- **rel_path**: Optional relative path within the media directory (e.g., "images/"). Must not contain ".." for security.

The file is saved to `{media_path}/{rel_path}/{filename}`. Returns a download URL.
""",
)
async def upload_file(file: UploadFile = File(...), rel_path: str = ""):
    if ".." in rel_path:
        raise HTTPException(status_code=400, detail="Invalid rel_path: contains '..'")
    file_size = 0
    content = await file.read()
    file_size = len(content)
    if file_size > config.max_upload_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {file_size} bytes > {config.max_upload_size} bytes",
        )
    logging.debug(
        f"Uploading file: {file.filename}, rel_path: {rel_path}, size: {file_size}"
    )
    os.makedirs(config.media_path, exist_ok=True)
    file_path = (
        os.path.join(config.media_path, rel_path, file.filename)
        if rel_path
        else os.path.join(config.media_path, file.filename)
    )
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)
    rel_path = os.path.relpath(file_path, config.media_path)
    url = f"{config.upload_base_url}/file?path={rel_path}"
    response = {"message": "File uploaded", "url": url}
    logging.debug(f"Response: {response}")
    return response


@app.get(
    "/api/file",
    tags=["Files"],
    summary="Download a file",
    description="""
Download a file from the media directory.

- **path**: The relative path to the file within the media directory (e.g., "images/photo.jpg"). Must not contain ".." for security.

Returns the file as a binary response.
""",
)
async def get_file(path: str):
    if ".." in path:
        raise HTTPException(status_code=400, detail="Invalid path: contains '..'")
    logging.debug(f"Requesting file: {path}")
    full_path = os.path.join(config.media_path, path)
    if os.path.exists(full_path):
        return FileResponse(full_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")


@app.get("/api/queue/length", tags=["Queue"])
async def get_queue_length(task_type: Optional[str] = None):
    logging.debug(f"Query params: task_type={task_type}")
    if task_type:
        queue = config.get_queue_for_task_type(task_type)
        length = redis_client.llen(queue)
        response = {f"queue_length_{task_type}": length}
    else:
        lengths = {}
        for t in ["test", "whisper"]:
            queue = config.get_queue_for_task_type(t)
            lengths[f"queue_length_{t}"] = redis_client.llen(queue)
        response = lengths
    logging.debug(f"Response: {response}")
    return response


@app.get(
    "/api/next_task",
    tags=["Queue"],
    summary="Get next pending task",
    description="Retrieves the next pending task from the queue, optionally filtered by task type. The task status is automatically updated to 'processing'.",
)
async def get_next_task(
    task_type: Optional[str] = Query(
        None,
        description="Filter tasks by type (e.g., 'test' for TTS, 'whisper' for transcription). If not specified, returns the next task of any type.",
    ),
):
    logging.debug(f"Getting next task for type: {task_type}")
    import asyncio

    queue = config.get_queue_for_task_type(task_type)
    task = await asyncio.to_thread(redis_client.blpop, queue, 0)
    if task:
        queue_name, task_data_str = task
        task_data = json.loads(task_data_str)
        response = {"task": task_data}
    else:
        response = {"task": None}
    logging.debug(f"Response: {response}")
    return response


@app.post("/api/whisper/audio/url", tags=["Whisper"])
async def submit_whisper_audio_url(req: WhisperRequest):
    logging.debug(f"Request body: {req.dict()}")
    task_id = models.insert_task({"url": req.url}, "whisper")
    queue_name = "tasks:whisper"
    task_for_queue = {
        "id": task_id,
        "payload": {"url": req.url},
        "task_type": "whisper-audio-url",
        "retry_time": 3,
    }
    try:
        redis_client.lpush(queue_name, json.dumps(task_for_queue))
        print(f"DEBUG: Created Whisper Audio URL task {task_id}")
        return {"task_id": task_id}
    except Exception as e:
        logging.error(f"Failed to submit whisper task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue task")


@app.post("/api/whisper/video/url", tags=["Whisper"])
async def submit_whisper_video_url(req: WhisperRequest):
    logging.debug(f"Request body: {req.dict()}")
    task_id = models.insert_task({"url": req.url}, "whisper")
    queue_name = "tasks:whisper"
    task_for_queue = {
        "id": task_id,
        "payload": {"url": req.url},
        "task_type": "whisper-video-url",
        "retry_time": 3,
    }
    try:
        redis_client.lpush(queue_name, json.dumps(task_for_queue))
        print(f"DEBUG: Created Whisper Video URL task {task_id}")
        return {"task_id": task_id}
    except Exception as e:
        logging.error(f"Failed to submit whisper task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue task")


@app.post("/api/whisper/audio/data", tags=["Whisper"])
async def submit_whisper_audio_data(file: UploadFile = File(...)):
    logging.debug(f"Uploading file: {file.filename}")
    os.makedirs(config.media_path, exist_ok=True)
    file_path = os.path.join(config.media_path, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    rel_path = os.path.relpath(file_path, config.media_path)
    task_id = models.insert_task({"rel_path": rel_path}, "whisper")
    queue_name = "tasks:whisper"
    task_for_queue = {
        "id": task_id,
        "payload": {"rel_path": rel_path},
        "task_type": "whisper-audio-data",
        "retry_time": 3,
    }
    try:
        redis_client.lpush(queue_name, json.dumps(task_for_queue))
        print(f"DEBUG: Created Whisper Audio Data task {task_id}")
        return {"task_id": task_id}
    except Exception as e:
        logging.error(f"Failed to submit whisper task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue task")


# --------------------
# __main__ 入口
# --------------------
if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="Run the API server")
    parser.add_argument(
        "--port", type=int, default=8989, help="Port to run the server on"
    )
    args = parser.parse_args()

    uvicorn.run(
        "api:app",  # 注意这里用字符串：模块名:app
        host="127.0.0.1",
        port=args.port,
        # reload=True,  # 开启自动重载
    )
