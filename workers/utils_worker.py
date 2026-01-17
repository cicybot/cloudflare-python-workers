import logging
import config
import requests
import time
import psutil
import platform
import threading


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


def register_worker(worker_id):
    # Report worker info
    platform_info = platform.platform()
    memory = psutil.virtual_memory()
    cpu_count = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0.0
    gpu_info = None  # TODO: Add GPU detection if needed
    while True:
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
            break  # Success, exit loop
        except Exception as e:
            logging.warning(
                f"Failed to register worker {worker_id}: {e}. Retrying in 5 seconds..."
            )
            time.sleep(5)  # Wait before retry
