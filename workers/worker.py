import uuid
import redis
import logging
import config
import requests
import json
import time


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
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# --------------------
# Config loaded from config.py
# --------------------
redis_url = config.redis_url


# --------------------
# Worker ID
# --------------------
WORKER_ID = str(uuid.uuid4())


# --------------------
# Redis client
# --------------------
redis_client = redis.from_url(redis_url, decode_responses=True)


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
    logging.info(f"Worker {WORKER_ID} started and waiting for tasks...")
    while True:
        # Listen to multiple queues
        task = redis_client.blpop(["tasks:index-tts", "tasks:voxcpm"], 0)
        if task:
            queue_name, task_data_str = task
            task_data = json.loads(task_data_str)
            pop_ts = time.time()
            push_ts = task_data.get("push_ts", pop_ts)
            queue_duration = pop_ts - push_ts
            logging.info(
                f"Received task from {queue_name} after {queue_duration:.2f}s in queue: {task_data}"
            )
            run_task(task_data)


# --------------------
# 启动
# --------------------
if __name__ == "__main__":
    run_tasks()
