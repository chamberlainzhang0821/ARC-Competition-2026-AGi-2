import re
import copy
import traceback
import numpy as np
import arc_dsl


def get_dsl_globals():
    """构建包含 np 和所有 arc_dsl 辅助函数的全局执行环境"""
    exec_globals = {
        "np": np,
        "numpy": np
    }
    for name in dir(arc_dsl):
        if not name.startswith("_"):
            exec_globals[name] = getattr(arc_dsl, name)
    return exec_globals


def extract_python_code(llm_response):
    """
    鲁棒地从 LLM 回复（包含 CoT 思考过程）中提取 Python 代码块。
    """
    if not llm_response:
        return None
        
    # 优先匹配 ```python ... ``` 代码块
    match = re.search(r"```python\s*(.*?)\s*```", llm_response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # 备用匹配 ``` ... ```
    match_generic = re.search(r"```\s*(.*?)\s*```", llm_response, re.DOTALL)
    if match_generic:
        return match_generic.group(1).strip()
    
    # 降级方案：按行查找 transform 函数块
    lines = llm_response.split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        if "def transform" in line or "import " in line:
            in_code = True
        if in_code:
            if line.startswith("This function") or line.startswith("Hope this") or line.startswith("Explanation"):
                break
            code_lines.append(line)
            
    if code_lines:
        return '\n'.join(code_lines)
        
    return None


def generate_diff_info(expected, actual):
    """生成 Output 矩阵与 Target 矩阵的差异诊断信息"""
    if not isinstance(actual, list) or not actual or not isinstance(actual[0], list):
        return f"Format Error: Output is not a valid 2D list. Got type: {type(actual)}"
        
    h_exp, w_exp = len(expected), len(expected[0]) if expected else 0
    h_act, w_act = len(actual), len(actual[0]) if actual else 0
    
    if (h_exp, w_exp) != (h_act, w_act):
        return f"Dimension Mismatch: Expected shape ({h_exp}x{w_exp}), but got ({h_act}x{w_act})."
        
    mismatches = []
    diff_count = 0
    for r in range(h_exp):
        for c in range(w_exp):
            if expected[r][c] != actual[r][c]:
                diff_count += 1
                if len(mismatches) < 8:  # 限制输出前 8 处差异，避免 Prompt 过长
                    mismatches.append(f"- At row {r}, col {c}: Expected {expected[r][c]}, Got {actual[r][c]}")
                    
    if diff_count > 8:
        mismatches.append(f"... and {diff_count - 8} more cell mismatches.")
        
    return f"Total Mismatched Cells: {diff_count}/{h_exp * w_exp}\n" + "\n".join(mismatches)


def execute_generated_code(python_code, input_grid):
    """
    在隔离环境（注入 DSL）中执行 LLM 生成的代码，防止污染原输入对象。
    """
    exec_globals = get_dsl_globals()
    local_env = {}
    input_copy = copy.deepcopy(input_grid)
    
    try:
        # 执行定义代码块
        exec(python_code, exec_globals, local_env)
        
        if 'transform' not in local_env and 'transform' not in exec_globals:
            return None, "Function 'transform' not found in generated code."
            
        transform_func = local_env.get('transform') or exec_globals.get('transform')
        
        # 调用 transform 函数
        output = transform_func(input_copy)
        
        # 将 numpy ndarray 统一转换为 python standard list
        if isinstance(output, np.ndarray):
            output = output.tolist()
            
        return output, "Success"
        
    except Exception as e:
        error_trace = traceback.format_exc(limit=2)
        return None, f"Runtime Exception: {str(e)}\n{error_trace}"


def evaluate_on_train_set(code, train_examples):
    """
    在所有 Train 示例上测试代码，返回 (是否通过, 错误总结, 详细 Diff 信息)。
    """
    for idx, example in enumerate(train_examples):
        inp = example["input"]
        expected = example["output"]
        
        predicted, status = execute_generated_code(code, inp)
        
        if status != "Success":
            eval_msg = f"Train Example {idx + 1} Failed during execution."
            diff_info = f"Execution Failure Detail:\n{status}"
            return False, eval_msg, diff_info
            
        if predicted != expected:
            eval_msg = f"Train Example {idx + 1} Output Logic Mismatch."
            diff_info = generate_diff_info(expected, predicted)
            return False, eval_msg, diff_info
            
    return True, "All training examples passed successfully!", ""


def run_on_test_set(code, test_examples):
    """
    在 Test 示例上运行通过的代码并打出预测结果。
    """
    print("\n--- Running on Test Example(s) ---")
    for t_idx, test_ex in enumerate(test_examples):
        test_pred, status = execute_generated_code(code, test_ex["input"])
        
        if status != "Success":
            print(f"❌ Test Example {t_idx + 1} Execution Error: {status}")
            continue
            
        print(f"Test Example {t_idx + 1} Prediction Matrix:")
        for row in test_pred:
            print(" ".join(str(cell) for cell in row))
            
        if "output" in test_ex:
            if test_pred == test_ex["output"]:
                print("🎉 Test Prediction MATCHES Ground Truth!")
            else:
                print("❌ Test Prediction MISMATCHED Ground Truth.")
