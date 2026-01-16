import json
from worker import run_task, run_tasks, redis_client


def test_run_task():
    """Test that run_task prints the task data."""
    task_data = {"action": "test", "payload": {"number": 2}}
    redis_client.lpush("tasks:index-tts", json.dumps(task_data))


def test_get_queue_length():
    """Test getting the length of the tasks queue."""
    length = redis_client.llen("tasks:index-tts")
    print(f"Queue length: {length}")
