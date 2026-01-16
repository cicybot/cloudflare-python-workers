import json
import time
import uuid
from pathlib import Path
import redis

import soundfile as sf
import numpy as np
from voxcpm import VoxCPM

# --------------------
# 任务存储路径
# --------------------
TASK_FOLDER = Path("./tasks")
TASK_FOLDER.mkdir(parents=True, exist_ok=True)

# --------------------
# Worker ID
# --------------------
WORKER_ID = str(uuid.uuid4())
print(f"[VoxCPM Worker {WORKER_ID}] Starting worker...")

# --------------------
# Redis client
# --------------------
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

# --------------------
# 初始化 VoxCPM 模型并 warmup
# --------------------
print(f"[VoxCPM Worker {WORKER_ID}] Loading VoxCPM model...")
tts_model = VoxCPM.from_pretrained("openbmb/VoxCPM1.5")
print(f"[VoxCPM Worker {WORKER_ID}] Model loaded. Warmup starting...")

# warmup
warmup_path = TASK_FOLDER / "voxcpm_warmup.wav"
wav = tts_model.generate(
    text="Warmup",
    prompt_wav_path="examples/voice_01.wav",
    prompt_text="Warmup",
    cfg_value=2.0,
    inference_timesteps=10,
    normalize=False,
    denoise=False,
    retry_badcase=True,
    retry_badcase_max_times=3,
    retry_badcase_ratio_threshold=6.0,
)
sf.write(str(warmup_path), wav, tts_model.tts_model.sample_rate)
print(f"[VoxCPM Worker {WORKER_ID}] Warmup done: {warmup_path}")


# --------------------
# 处理单个 VoxCPM 任务（带详细日志）
# --------------------
def run_voxcpm_task(task_data):
    # 只处理 VoxCPM 类型的任务
    task_type = task_data.get("type")
    if task_type != "voxcpm":
        return

    if task_data.get("status") != "pending":
        print(
            f"[VoxCPM Worker {WORKER_ID}] Skipping task {task_data.get('id')} (status: {task_data.get('status')})"
        )
        return

    task_id = task_data["id"]
    task_params = task_data["params"]

    # 自动生成 output_path 如果未提供
    if "output_path" not in task_params:
        task_params["output_path"] = str(TASK_FOLDER / f"{task_id}.wav")

    # 默认参数处理
    if "text" not in task_params:
        task_params["text"] = "Hello world"

    # 如果缺少 prompt_wav_path，使用默认
    if "spk_audio_prompt" in task_params and "prompt_wav_path" not in task_params:
        task_params["prompt_wav_path"] = task_params["spk_audio_prompt"]
    elif "prompt_wav_path" not in task_params:
        task_params["prompt_wav_path"] = "examples/voice_01.wav"
        print(
            f"[VoxCPM Worker {WORKER_ID}] Task {task_id} missing prompt_wav_path, using default."
        )

    # 如果缺少 prompt_text，使用默认或从 text 复制
    if "prompt_text" not in task_params:
        task_params["prompt_text"] = task_params.get("text", "Hello world")
        print(
            f"[VoxCPM Worker {WORKER_ID}] Task {task_id} missing prompt_text, using text."
        )

    # 默认生成参数
    defaults = {
        "cfg_value": 2.0,
        "inference_timesteps": 10,
        "normalize": False,
        "denoise": False,
        "retry_badcase": True,
        "retry_badcase_max_times": 3,
        "retry_badcase_ratio_threshold": 6.0,
    }
    for key, default_value in defaults.items():
        if key not in task_params:
            task_params[key] = default_value

    # 更新状态为 running
    task_data["status"] = "running"
    task_data["worker_id"] = WORKER_ID
    task_data["start_time"] = time.time()
    redis_client.set(
        f"task:{task_id}", json.dumps(task_data, ensure_ascii=False, indent=2)
    )
    redis_client.srem("status:pending", task_id)
    redis_client.sadd("status:running", task_id)
    print(
        f"[VoxCPM Worker {WORKER_ID}] [RUNNING] Task {task_id} started at {task_data['start_time']:.2f}"
    )

    try:
        # 调用 VoxCPM 生成音频
        print(
            f"[VoxCPM Worker {WORKER_ID}] [INFO] Generating audio for task {task_id}..."
        )
        wav = tts_model.generate(
            text=task_params["text"],
            prompt_wav_path=task_params["prompt_wav_path"],
            prompt_text=task_params["prompt_text"],
            cfg_value=task_params["cfg_value"],
            inference_timesteps=task_params["inference_timesteps"],
            normalize=task_params["normalize"],
            denoise=task_params["denoise"],
            retry_badcase=task_params["retry_badcase"],
            retry_badcase_max_times=task_params["retry_badcase_max_times"],
            retry_badcase_ratio_threshold=task_params["retry_badcase_ratio_threshold"],
        )

        # 保存音频
        sf.write(task_params["output_path"], wav, tts_model.tts_model.sample_rate)

        # 更新状态为 done
        task_data["status"] = "done"
        task_data["result"] = task_params["output_path"]
        task_data["end_time"] = time.time()
        task_data["duration"] = task_data["end_time"] - task_data["start_time"]
        redis_client.set(
            f"task:{task_id}", json.dumps(task_data, ensure_ascii=False, indent=2)
        )
        redis_client.srem("status:running", task_id)
        redis_client.sadd("status:done", task_id)
        print(
            f"[VoxCPM Worker {WORKER_ID}] [DONE] Task {task_id} completed in {task_data['duration']:.2f}s, output: {task_params['output_path']}"
        )

    except Exception as e:
        # 更新状态为 error
        task_data["status"] = "error"
        task_data["error"] = str(e)
        task_data["end_time"] = time.time()
        task_data["duration"] = task_data["end_time"] - task_data.get(
            "start_time", task_data["end_time"]
        )
        redis_client.set(
            f"task:{task_id}", json.dumps(task_data, ensure_ascii=False, indent=2)
        )
        redis_client.srem("status:running", task_id)
        redis_client.sadd("status:error", task_id)
        print(
            f"[VoxCPM Worker {WORKER_ID}] [ERROR] Task {task_id} failed after {task_data['duration']:.2f}s: {e}"
        )


# --------------------
# 无限循环扫描任务
# --------------------
def run_task(poll_interval=1.0):
    print(f"[VoxCPM Worker {WORKER_ID}] Worker loop started")
    while True:
        task_ids = redis_client.smembers("status:pending")
        for tid in task_ids:
            task_data_str = redis_client.get(f"task:{tid}")
            if task_data_str:
                task_data = json.loads(task_data_str)
                if task_data.get("type") == "voxcpm":
                    run_voxcpm_task(task_data)

        time.sleep(poll_interval)


# --------------------
# 启动
# --------------------
if __name__ == "__main__":
    run_task()
