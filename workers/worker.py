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


def update_task_with_retry(task_id, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{config.api_url}/update_task", json=data, timeout=5
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logging.warning(f"Attempt {attempt + 1} failed for task {task_id}: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait before retry
    logging.error(f"Failed to update task {task_id} after {max_retries} attempts")
    return False


logging.basicConfig(
    level=getattr(logging, config.log_level),
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
)


def heartbeat_worker(worker_id):
    while True:
        try:
            memory = psutil.virtual_memory()
            response = requests.post(
                f"{config.api_url}/update_worker",
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
    max_processing_retries = task_data.get("retry_time", 3)

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

    for retry in range(max_processing_retries):
        try:
            # Simulate processing
            logging.debug(f"Processing task data: {task_data}")

            # Calculate duration and set result
            end_time = time.time()
            duration = end_time - start_time

            task_result = {"output": "processed", "duration": duration}

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
            break  # Success, exit retry loop

        except Exception as e:
            logging.warning(
                f"Processing attempt {retry + 1} failed for task {task_id}: {e}"
            )
            if retry < max_processing_retries - 1:
                time.sleep(2)  # Wait before retry
            else:
                logging.error(
                    f"Failed to process task {task_id} after {max_processing_retries} attempts: {e}"
                )
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


def run_tasks():
    logging.info(f"Worker {WORKER_ID} started and polling for tasks...")
    while True:
        try:
            response = requests.get(
                f"{config.api_url}/api/next_task?task_type=test", timeout=5
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
        except requests.RequestException as e:
            logging.error(f"Error polling for tasks: {e}")
            time.sleep(config.poll_interval)


# --------------------
# 启动
# --------------------
if __name__ == "__main__":
    run_tasks()
