import mysql.connector
import json
import config
import uuid


def get_db_connection():
    return mysql.connector.connect(
        host=config.mysql_host,
        user=config.mysql_user,
        password=config.mysql_password,
        database=config.mysql_database,
    )


def insert_task(task_data, task_type):
    task_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (id, data, task_type) VALUES (%s, %s, %s)",
        (task_id, json.dumps(task_data), task_type),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return task_id


def get_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, status, data, created_at, updated_at, duration, error_msg, retry_time, task_result, task_type FROM tasks WHERE id = %s",
        (task_id,),
    )
    task = cursor.fetchone()
    cursor.close()
    conn.close()
    return task


def get_tasks_by_status(status):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, status, data, created_at, updated_at, duration, error_msg, retry_time, task_result, task_type FROM tasks WHERE status = %s",
        (status,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def update_task_status(task_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = %s WHERE id = %s", (status, task_id))
    conn.commit()
    cursor.close()
    conn.close()


def update_task(task_id, **kwargs):
    if not kwargs:
        return
    set_clause = ", ".join(f"{k} = %s" for k in kwargs.keys())
    values = list(kwargs.values()) + [task_id]
    query = f"UPDATE tasks SET {set_clause} WHERE id = %s"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()


def insert_worker(
    worker_id,
    platform,
    memory_total,
    memory_available,
    cpu_count,
    cpu_freq,
    gpu_info=None,
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO workers (id, platform, memory_total, memory_available, cpu_count, cpu_freq, gpu_info) VALUES (%s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE platform=VALUES(platform), memory_total=VALUES(memory_total), memory_available=VALUES(memory_available), cpu_count=VALUES(cpu_count), cpu_freq=VALUES(cpu_freq), gpu_info=VALUES(gpu_info)",
        (
            worker_id,
            platform,
            memory_total,
            memory_available,
            cpu_count,
            cpu_freq,
            gpu_info,
        ),
    )
    conn.commit()
    cursor.close()
    conn.close()


def update_worker(worker_id, **kwargs):
    if not kwargs:
        return
    set_clause = ", ".join(f"{k} = %s" for k in kwargs.keys())
    values = list(kwargs.values()) + [worker_id]
    query = f"UPDATE workers SET {set_clause} WHERE id = %s"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()


def get_tasks(task_type=None, status=None, limit=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if task_type:
        query += " AND task_type = %s"
        params.append(task_type)
    if status:
        query += " AND status = %s"
        params.append(status)
    query += " ORDER BY created_at DESC"
    if limit is not None:
        query += " LIMIT %s"
        params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    # For total, count without limit
    count_query = "SELECT COUNT(*) as total FROM tasks WHERE 1=1"
    count_params = []
    if task_type:
        count_query += " AND task_type = %s"
        count_params.append(task_type)
    if status:
        count_query += " AND status = %s"
        count_params.append(status)
    cursor.execute(count_query, count_params)
    total = cursor.fetchone()["total"]

    # Format tasks like the removed get_all_tasks
    tasks = []
    for row in rows:
        params = json.loads(row["data"]) if row["data"] else {}
        task_data = {
            "id": row["id"],
            "task_type": row["task_type"],
            "params": params,
            "status": row["status"],
            "result": (
                row["task_result"]["output"]
                if row["task_result"] and "output" in row["task_result"]
                else None
            ),
            "worker_id": None,  # Not tracked
            "submit_time": row["created_at"].timestamp() if row["created_at"] else None,
            "start_time": None,  # Not tracked
            "end_time": row["updated_at"].timestamp() if row["updated_at"] else None,
            "duration": row["duration"],
            "error_msg": row["error_msg"],
            "retry_time": row["retry_time"],
            "task_result": row["task_result"],
        }
        tasks.append(task_data)

    conn.close()
    return {"total": total, "tasks": tasks}


def get_all_workers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM workers")
    workers = cursor.fetchall()
    conn.close()
    return workers
