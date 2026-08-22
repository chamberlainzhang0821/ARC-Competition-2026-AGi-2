import os
import sys
import time
import hashlib
import requests
from datetime import datetime
from prompt_builder import build_task_prompt, build_feedback_prompt
from data_loader import load_arc_data
from code_executor import (
    extract_python_code,
    evaluate_on_train_set,
    run_on_test_set
)

# this is the entry point for the ARC benchmark batch run, which processes 50 tasks in sequence and logs the results.



# ==========================================
# 0. Logger setup (Tee Terminal Output to File)
# ==========================================
class DualLogger:
    """同时向控制台 (stdout) 和 .txt 日志文件写入内容"""
    def __init__(self, filepath):
        self.terminal = sys.stdout
        self.log_file = open(filepath, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()


# ==========================================
# 1. Call Local LLM (Dynamic Temperature)
# ==========================================
def query_local_llama(prompt, temperature=0.0, model="llama3"):
    """
    Send the prompt to the local Ollama API with dynamic temperature.
    """
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature} 
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to local LLM: {e}")
        return None


# ==========================================
# 2. Task Solver Engine (Stateful Feedback Loop)
# ==========================================
def solve_arc_task(task_id, task_data, max_retries=10, model_name="llama3"):
    """
    Solves a single ARC task using LLM with deduplication & dynamic feedback.
    Returns: (is_success, total_attempts_used)
    """
    print(f"\n==========================================")
    print(f"🧩 Solving Task ID: {task_id}")
    print(f"==========================================")
    
    task_cache = {
        "tried_hashes": set(),
        "last_failed_code": None,
        "last_error_msg": None,
        "last_diff_info": ""
    }
    
    attempt = 1
    
    while attempt <= max_retries:
        current_temp = 0.0 if attempt == 1 else 0.2
        print(f"\n--- ATTEMPT {attempt}/{max_retries} (Temp: {current_temp}) ---")
        
        if attempt == 1:
            current_prompt = build_task_prompt(task_data)
        else:
            error_with_instruction = (
                f"{task_cache['last_error_msg']}\n\n"
                "⚠️ CRITICAL INSTRUCTION: Your previous code structure HAS FAILED. "
                "Do NOT fix minor details or repeat the same syntax pattern. "
                "Completely pivot your approach (e.g., switch between matrix operations, "
                "connected component detection, or color mapping logic)."
            )
            current_prompt = build_feedback_prompt(
                task_data=task_data,
                failed_code=task_cache["last_failed_code"],
                error_message=error_with_instruction,
                diff_info=task_cache["last_diff_info"]
            )

        print(f"Asking Local LLM ({model_name})...")
        llm_reply = query_local_llama(current_prompt, temperature=current_temp, model=model_name) 
        if not llm_reply:
            print("No response from LLM. Aborting task.")
            return False, attempt
            
        code = extract_python_code(llm_reply)
        if not code:
            error_msg = "Failed to extract valid Python code block. Please wrap code in ```python ```."
            print(f"❌ {error_msg}")
            task_cache["last_failed_code"] = llm_reply
            task_cache["last_error_msg"] = error_msg
            task_cache["last_diff_info"] = ""
            attempt += 1
            continue
            
        # Code Hash 去重拦截
        code_hash = hashlib.md5(code.encode('utf-8')).hexdigest()
        if code_hash in task_cache["tried_hashes"]:
            print(f"⚠️ Duplicate code generated (Hash: {code_hash[:8]}). Re-sampling with temp 0.2...")
            retry_reply = query_local_llama(current_prompt, temperature=0.2, model=model_name)
            if retry_reply:
                code = extract_python_code(retry_reply)
                if code:
                    code_hash = hashlib.md5(code.encode('utf-8')).hexdigest()

        task_cache["tried_hashes"].add(code_hash)

        # 执行评估
        eval_result = evaluate_on_train_set(code, task_data["train"])
        
        if isinstance(eval_result, tuple):
            if len(eval_result) == 3:
                passed, eval_msg, diff_info = eval_result
            else:
                passed, eval_msg = eval_result
                diff_info = ""
        else:
            passed, eval_msg, diff_info = False, str(eval_result), ""
        
        if passed:
            print("✅ Status: SUCCESS! Passed all Train examples.")
            run_on_test_set(code, task_data["test"])
            return True, attempt
        else:
            print(f"❌ Status: FAILED.")
            print(f"Error: {eval_msg}")
            if diff_info:
                print(f"Diff Info:\n{diff_info}")
                
            task_cache["last_failed_code"] = code
            task_cache["last_error_msg"] = eval_msg
            task_cache["last_diff_info"] = diff_info

        attempt += 1

    print(f"\n🚨 Max retries reached for Task {task_id}. LLM failed to solve.")
    return False, max_retries


# ==========================================
# Main Execution Entry (Batch Processing 50 Tasks)
# ==========================================
if __name__ == "__main__":
    # 1. 创建 logs 文件夹并配置双向日志输出
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join("logs", f"arc_run_50tasks_{timestamp}.txt")
    
    sys.stdout = DualLogger(log_file_path)
    
    print(f"==========================================")
    print(f"🚀 Starting ARC Benchmark Batch Run")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📝 Logging to: {log_file_path}")
    print(f"==========================================")

    # 2. 加载数据集并截取前 50 道题
    print("\nLoading ARC Training Dataset...")
    tasks = load_arc_data("training")
    
    if not tasks:
        print("❌ No tasks loaded. Check Raw Data directory.")
    else:
        target_task_ids = list(tasks.keys())[:50]
        total_tasks = len(target_task_ids)
        print(f"Loaded {len(tasks)} total tasks. Running on first {total_tasks} tasks.\n")
        
        # 统计数据记录项
        success_tasks = []
        failed_tasks = []
        task_attempts = {}
        start_time = time.time()
        
        # 3. 循环测试 50 道题目
        for idx, tid in enumerate(target_task_ids, 1):
            print(f"\n>>>> Progress: Task {idx}/{total_tasks} (ID: {tid}) <<<<")
            is_solved, attempts_used = solve_arc_task(
                task_id=tid, 
                task_data=tasks[tid], 
                max_retries=10, 
                model_name="llama3"  # 换模型时在此修改，如 "qwen2.5-coder:32b"
            )
            
            task_attempts[tid] = attempts_used
            if is_solved:
                success_tasks.append(tid)
            else:
                failed_tasks.append(tid)

        # 4. 汇总终态报告并写入 txt 文件
        elapsed_time = time.time() - start_time
        avg_attempts = sum(task_attempts.values()) / total_tasks if total_tasks > 0 else 0
        success_rate = (len(success_tasks) / total_tasks) * 100 if total_tasks > 0 else 0
        
        print("\n" + "=" * 50)
        print("📊 BENCHMARK SUMMARY REPORT")
        print("=" * 50)
        print(f"Total Tasks Attempted : {total_tasks}")
        print(f"Successfully Solved   : {len(success_tasks)}")
        print(f"Failed Tasks          : {len(failed_tasks)}")
        print(f"Success Rate          : {success_rate:.2f}%")
        print(f"Average Attempts/Task : {avg_attempts:.2f}")
        print(f"Total Time Elapsed    : {elapsed_time / 60:.2f} minutes")
        print("-" * 50)
        print(f"✅ Successful Task IDs:\n{success_tasks}")
        print("-" * 50)
        print(f"❌ Failed Task IDs:\n{failed_tasks}")
        print("=" * 50)
        print(f"\nComplete logs saved to: {log_file_path}")
