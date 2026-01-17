import uuid
import logging
import config
import requests
import json
import time
import sys
import psutil
import platform
import threading
import tempfile
import subprocess
import requests as req
import os
import whisper
import torch

# --------------------
# Config loaded from config.py
# --------------------
# Redis not used directly


def heartbeat_worker(worker_id):
    while True:
        try:
            memory = psutil.virtual_memory()
            response = requests.post(
                f"{config.api_url}/api/update_worker",
                json={"worker_id": worker_id, "memory_available": memory.available},
                timeout=5,
            )
            response.raise_for_status()
            logging.debug(f"Worker {worker_id} heartbeat sent")
        except Exception as e:
            logging.error(f"Failed to send heartbeat for worker {worker_id}: {e}")
        time.sleep(config.report_interval)


# --------------------
# Worker ID
# --------------------
worker_id = sys.argv[1] if len(sys.argv) > 1 else str(uuid.uuid4())
WORKER_ID = worker_id

# Load Whisper model
model = whisper.load_model("base")
if torch.cuda.is_available():
    model.to("cuda")

# Report worker info
platform_info = platform.platform()
memory = psutil.virtual_memory()
cpu_count = psutil.cpu_count(logical=True)
cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0.0
gpu_info = None  # TODO: Add GPU detection if needed
try:
        response = requests.post(
            f"{config.api_url}/api/register_worker",
            json={
            "worker_id": worker_id,
            "platform": platform_info,
            "memory_total": memory.total,
            "memory_available": memory.available,
            "cpu_count": cpu_count,
            "cpu_freq": cpu_freq,
            "gpu_info": gpu_info,
        },
        timeout=5,
    )
    response.raise_for_status()
    logging.info(f"Worker {worker_id} registered with system info")
    # Start heartbeat thread
    heartbeat_thread = threading.Thread(
        target=heartbeat_worker, args=(worker_id,), daemon=True
    )
    heartbeat_thread.start()
except Exception as e:
    logging.error(f"Failed to register worker {worker_id}: {e}")
    sys.exit(1)


def run_task(task_data):
    logging.info(f"Processing task: {task_data}")
    start_time = time.time()
    task_id = task_data.get("id")
    payload = task_data.get("payload", {})
    task_type = task_data.get("task_type", "unknown")

    # Update status to processing
    if task_id:
        success = update_task_with_retry(
            task_id, {"task_id": task_id, "status": "processing"}
        )
        if not success:
            # If can't even update to processing, fail
            update_task_with_retry(
                task_id,
                {
                    "task_id": task_id,
                    "status": "failed",
                    "error_msg": "Failed to start processing",
                },
            )
            return

    try:
        if task_type == "whisper-audio-url":
            url = payload["url"]
            # download file
            r = req.get(url, stream=True)
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".audio") as tmp:
                for chunk in r.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                tmp_path = tmp.name
        elif task_type == "whisper-video-url":
            url = payload["url"]
            # download video
            r = req.get(url, stream=True)
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
                for chunk in r.iter_content(chunk_size=8192):
                    tmp_video.write(chunk)
                video_path = tmp_video.name
            # convert to audio
            audio_fd, audio_path = tempfile.mkstemp(suffix=".mp3")
            os.close(audio_fd)
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-vn",
                "-acodec",
                "libmp3lame",
                "-q:a",
                "2",
                audio_path,
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            tmp_path = audio_path
        elif task_type == "whisper-audio-data":
            rel_path = payload["rel_path"]
            tmp_path = os.path.join(config.media_path, rel_path)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

        size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        # transcribe
        result = model.transcribe(tmp_path)
        text = result["text"]

        # Calculate duration and set result
        end_time = time.time()
        duration = end_time - start_time
        task_result = {
            "text": text,
            "file_size_mb": round(size_mb, 2),
            "exec_time_sec": round(duration, 2),
        }

        # Update status to completed with additional fields
        if task_id:
            update_task_with_retry(
                task_id,
                {
                    "task_id": task_id,
                    "status": "completed",
                    "duration": duration,
                    "task_result": task_result,
                },
            )

    except Exception as e:
        logging.error(f"Error processing task {task_id}: {e}")
        # Update status to failed with error_msg
        if task_id:
            update_task_with_retry(
                task_id,
                {
                    "task_id": task_id,
                    "status": "failed",
                    "error_msg": str(e),
                },
            )


def update_task_with_retry(task_id, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{config.api_url}/api/update_task", json=data, timeout=5
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logging.warning(f"Attempt {attempt + 1} failed for task {task_id}: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait before retry
    logging.error(f"Failed to update task {task_id} after {max_retries} attempts")
    return False


def run_tasks():
    logging.info(f"Worker {WORKER_ID} started and polling for tasks...")
    while True:
        try:
            response = requests.get(
                f"{config.api_url}/api/next_task?task_type=whisper", timeout=5
            )
            response.raise_for_status()
            data = response.json()
            if data["task"]:
                task_data = data["task"]
                pop_ts = time.time()
                push_ts = task_data.get("push_ts", pop_ts)
                queue_duration = pop_ts - push_ts
                logging.info(
                    f"Received task after {queue_duration:.2f}s in queue: {task_data}"
                )
                run_task(task_data)
            else:
                time.sleep(config.poll_interval)
        except requests.RequestException as e:
            logging.warning(f"Error polling for tasks, retrying: {e}")
            time.sleep(1)  # Short retry delay


if __name__ == "__main__":
    run_tasks()
