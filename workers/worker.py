import uuid
import logging
import config
import requests
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils_worker import update_task_with_retry, register_worker


logging.basicConfig(
    level=getattr(logging, config.log_level),
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
)


# --------------------
# Worker ID
# --------------------
worker_id = sys.argv[1] if len(sys.argv) > 1 else str(uuid.uuid4())
WORKER_ID = worker_id

# Register worker and start heartbeat
register_worker(worker_id)


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
