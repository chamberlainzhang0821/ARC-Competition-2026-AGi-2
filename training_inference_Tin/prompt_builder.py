import os
import sys
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from features import extract_macro_features, extract_all_objects 
from rule_detector import detect_all_rules


def stringify_grid(grid):
    """将矩阵转为 2D ASCII 空格分隔形式"""
    return "\n".join(" ".join(str(cell) for cell in row) for row in grid)


def describe_grid(grid, label="Input"):
    grid_np = np.array(grid)
    shape_str = f"{grid_np.shape[0]}x{grid_np.shape[1]}"
    
    macro_feats = extract_macro_features(grid_np) 
    objects = extract_all_objects(grid_np) 
    
    colors = set([obj['color'] for obj in objects])
    color_str = ", ".join(map(str, colors)) if colors else "None"
    
    description = (
        f"--- {label} Grid (Size: {shape_str}) ---\n"
        f"Matrix:\n{stringify_grid(grid)}\n"
        f"Features: {macro_feats['num_components']} objects, colors [{color_str}], "
        f"symmetry score: {macro_feats['symmetry_score']}\n"
    )
    return description


def get_dsl_documentation():
    """
    提供 DSL 辅助函数文档，自动注入 Prompt，引导 LLM 直接调用以减少越界错误。
    """
    doc = (
        "=== PRE-LOADED HELPER FUNCTIONS (DSL) ===\n"
        "You can directly call these helper functions inside your `transform` function (no imports needed):\n"
        "- `recolor(grid, color_map)`: Maps colors according to a dict, e.g., recolor(grid, {5: 1, 0: 2})\n"
        "- `repeat_tile(grid, row_repeats, col_repeats)`: Tiles/repeats the grid along rows and columns.\n"
        "- `scale_up(grid, row_scale, col_scale)`: Scales up each cell by integer row/column factors.\n"
        "- `kronecker_expand(grid, pattern)`: Expands non-zero cells in `grid` using `pattern`.\n"
        "- `apply_gravity(grid, direction='down')`: Simulates gravity dropping non-zero cells to the bottom.\n"
        "- `rotate_90(grid)`, `rotate_180(grid)`, `rotate_270(grid)`: Rotates the grid clockwise.\n"
        "- `reflect_horizontal(grid)`, `reflect_vertical(grid)`: Flips grid horizontally or vertically.\n"
        "- `crop(grid, top, left, height, width)`: Crops a subgrid starting at (top, left).\n\n"
    )
    return doc


def extract_task_hints(task_data):
    hints = []
    for i, example in enumerate(task_data["train"]):
        inp, out = example["input"], example["output"]
        inp_shape = f"{len(inp)}x{len(inp[0])}"
        out_shape = f"{len(out)}x{len(out[0])}"
        
        # 显式加入尺寸变换元数据 (Grid Size Metadata)
        hints.append(f"Example {i+1} Grid Size Transition: {inp_shape} -> {out_shape}")
        
        rules = detect_all_rules(inp, out)
        if rules.get("tile_repeat"):
            hints.append(f"Example {i+1} Tile Repeat: {rules['tile_repeat']}")
        if rules.get("scale_up"):
            hints.append(f"Example {i+1} Scaling: {rules['scale_up']}")
        if rules.get("rotation"):
            hints.append(f"Example {i+1} Rotated {rules['rotation']} deg")
        if rules.get("reflection"):
            hints.append(f"Example {i+1} Reflected ({rules['reflection']})")
        if rules.get("color_substitution"):
            hints.append(f"Example {i+1} Color Mapping: {rules['color_substitution']['mapping']}")
        if rules.get("gravity"):
            hints.append(f"Example {i+1} Gravity: direction {rules['gravity']['direction']}")
        if rules.get("flood_fill"):
            hints.append(f"Example {i+1} Flood Fill: target colors {rules['flood_fill']['filled_colors']}")
            
    return hints


def build_task_prompt(task_data):
    prompt = "You are an expert Python programmer solving ARC grid transformation puzzles.\n\n"
    
    # 🌟 强制 CoT 思考步骤要求
    prompt += "=== THINKING PROCESS (Chain-of-Thought) ===\n"
    prompt += "Before writing any code, you MUST analyze the task in 3 steps:\n"
    prompt += "1. Pattern Analysis: Observe grid dimensions, background, color distributions, and shapes.\n"
    prompt += "2. Logical Rule: State the exact transformation algorithm in plain English.\n"
    prompt += "3. Strategy: Decide which DSL helper functions (e.g. recolor, apply_gravity, repeat_tile) to call.\n\n"

    # 1. 注入 DSL 工具函数文档
    prompt += get_dsl_documentation()

    # 2. 注入规则引擎检测到的特征线索
    detected_hints = extract_task_hints(task_data)
    if detected_hints:
        prompt += "=== DETECTED PATTERN & SIZE METADATA ===\n"
        for hint in detected_hints:
            prompt += f"- {hint}\n"
        prompt += "\n"

    # 3. 构造 2D 网格与特征描述
    for i, example in enumerate(task_data["train"]):
        prompt += f"=== Example {i + 1} ===\n"
        prompt += describe_grid(example["input"], label="Input")
        prompt += describe_grid(example["output"], label="Output")
        prompt += "\n"
        
    prompt += "=== STRICT REQUIREMENTS ===\n"
    prompt += "1. Write your Chain-of-Thought analysis FIRST.\n"
    prompt += "2. THEN, write the Python solution wrapped strictly inside ```python ``` blocks.\n"
    prompt += "3. `input_grid` is a 2D list of INTEGERS (0-9). `transform()` must return a 2D list of INTEGERS (0-9).\n"
    prompt += "4. HIGHLY RECOMMENDED: Use the pre-loaded DSL helper functions (recolor, repeat_tile, scale_up, apply_gravity, etc.).\n"
    
    return prompt



def build_feedback_prompt(task_data, failed_code, error_message, diff_info=""):
    """支持 Traceback 和 Diff 信息的闭环反馈模板"""
    prompt = build_task_prompt(task_data)
    
    prompt += "\n=== PREVIOUS ATTEMPT FAILED ===\n"
    prompt += f"Your previous code:\n```python\n{failed_code}\n```\n\n"
    prompt += f"Error/Traceback:\n{error_message}\n\n"
    
    if diff_info:
        prompt += f"Execution Output Mismatch (Diff):\n{diff_info}\n\n"
        
    prompt += "=== TASK REVISION ===\n"
    prompt += "Fix the logic and boundary conditions. Leverage the pre-loaded DSL helper functions if appropriate. Output ONLY corrected code inside ```python ``` blocks."
    
    return prompt
