import argparse
import json
import os
from collections import Counter

from operation import execute_program, validate_grid


RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "Raw Data")


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def same_shape(a, b):
    return len(a) == len(b) and len(a[0]) == len(b[0])


def rotate_grid(grid, angle):
    return execute_program(grid, [{"name": "rotate", "parameters": {"angle": angle}}])


def flip_grid(grid, axis):
    return execute_program(grid, [{"name": "flip", "parameters": {"axis": axis}}])


def infer_color_mapping(input_grid, output_grid):
    if not same_shape(input_grid, output_grid):
        return None

    mapping = {}
    changed = False
    for row in range(len(input_grid)):
        for col in range(len(input_grid[0])):
            source = input_grid[row][col]
            target = output_grid[row][col]
            if source in mapping and mapping[source] != target:
                return None
            mapping[source] = target
            changed = changed or source != target

    return mapping if changed else None


def find_crop_params(input_grid, output_grid):
    input_height = len(input_grid)
    input_width = len(input_grid[0])
    output_height = len(output_grid)
    output_width = len(output_grid[0])
    if output_height > input_height or output_width > input_width:
        return []

    matches = []
    for top in range(input_height - output_height + 1):
        for left in range(input_width - output_width + 1):
            cropped = [row[left:left + output_width] for row in input_grid[top:top + output_height]]
            if cropped == output_grid:
                matches.append({"top": top, "left": left, "height": output_height, "width": output_width})
    return matches


def foreground_bbox(grid, background=0):
    cells = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] != background
    ]
    if not cells:
        return None
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return {
        "top": min(rows),
        "left": min(cols),
        "height": max(rows) - min(rows) + 1,
        "width": max(cols) - min(cols) + 1,
    }


def infer_scale_params(input_grid, output_grid):
    input_height = len(input_grid)
    input_width = len(input_grid[0])
    output_height = len(output_grid)
    output_width = len(output_grid[0])
    if output_height % input_height or output_width % input_width:
        return None

    row_scale = output_height // input_height
    col_scale = output_width // input_width
    if row_scale == 1 and col_scale == 1:
        return None

    program = [{"name": "scale", "parameters": {"row_scale": row_scale, "col_scale": col_scale}}]
    return {"row_scale": row_scale, "col_scale": col_scale} if execute_program(input_grid, program) == output_grid else None


def infer_tile_params(input_grid, output_grid):
    input_height = len(input_grid)
    input_width = len(input_grid[0])
    output_height = len(output_grid)
    output_width = len(output_grid[0])
    if output_height % input_height or output_width % input_width:
        return None

    rows = output_height // input_height
    cols = output_width // input_width
    if rows == 1 and cols == 1:
        return None

    program = [{"name": "tile", "parameters": {"rows": rows, "cols": cols}}]
    return {"rows": rows, "cols": cols} if execute_program(input_grid, program) == output_grid else None


def infer_translation_params(input_grid, output_grid):
    if not same_shape(input_grid, output_grid):
        return None

    height = len(input_grid)
    width = len(input_grid[0])
    for row_shift in range(-(height - 1), height):
        for col_shift in range(-(width - 1), width):
            if row_shift == 0 and col_shift == 0:
                continue
            program = [{
                "name": "translate",
                "parameters": {"row_shift": row_shift, "col_shift": col_shift, "fill_color": 0},
            }]
            if execute_program(input_grid, program) == output_grid:
                return {"row_shift": row_shift, "col_shift": col_shift, "fill_color": 0}
    return None


def candidate_programs_from_pair(input_grid, output_grid):
    candidates = []

    if input_grid == output_grid:
        candidates.append([{"name": "identity", "parameters": {}}])

    for angle in (90, 180, 270):
        if rotate_grid(input_grid, angle) == output_grid:
            candidates.append([{"name": "rotate", "parameters": {"angle": angle}}])

    for axis in ("horizontal", "vertical"):
        if flip_grid(input_grid, axis) == output_grid:
            candidates.append([{"name": "flip", "parameters": {"axis": axis}}])

    for params in find_crop_params(input_grid, output_grid):
        candidates.append([{"name": "crop", "parameters": params}])

    bbox = foreground_bbox(input_grid)
    if bbox and execute_program(input_grid, [{"name": "crop", "parameters": bbox}]) == output_grid:
        candidates.append([{"name": "crop_non_background", "parameters": {"background": 0}}])

    scale_params = infer_scale_params(input_grid, output_grid)
    if scale_params:
        candidates.append([{"name": "scale", "parameters": scale_params}])

    tile_params = infer_tile_params(input_grid, output_grid)
    if tile_params:
        candidates.append([{"name": "tile", "parameters": tile_params}])

    translation_params = infer_translation_params(input_grid, output_grid)
    if translation_params:
        candidates.append([{"name": "translate", "parameters": translation_params}])

    color_mapping = infer_color_mapping(input_grid, output_grid)
    if color_mapping:
        candidates.append([{"name": "replace_colors", "parameters": {"mapping": color_mapping}}])

    return candidates


def program_key(program):
    return json.dumps(program, sort_keys=True)


def verify_program(train_pairs, program):
    matches = 0
    for pair in train_pairs:
        try:
            prediction = execute_program(pair["input"], program)
        except Exception:
            return False, 0
        if prediction == pair["output"]:
            matches += 1
    return matches == len(train_pairs), matches


def infer_programs(task):
    train_pairs = task["train"]
    if not train_pairs:
        return []

    seen = set()
    verified = []
    for program in candidate_programs_from_pair(train_pairs[0]["input"], train_pairs[0]["output"]):
        key = program_key(program)
        if key in seen:
            continue
        seen.add(key)
        ok, matches = verify_program(train_pairs, program)
        if ok:
            verified.append({"program": program, "train_matches": matches})

    return verified


def blank_like(grid):
    return [[0 for _ in row] for row in grid]


def select_two_attempts(task, programs, test_input):
    attempts = []
    for item in programs:
        try:
            prediction = execute_program(test_input, item["program"])
        except Exception:
            continue
        if validate_grid(prediction) and prediction not in attempts:
            attempts.append(prediction)
        if len(attempts) == 2:
            break

    for fallback in (test_input, blank_like(test_input)):
        if fallback not in attempts:
            attempts.append(fallback)
        if len(attempts) == 2:
            break

    while len(attempts) < 2:
        attempts.append(blank_like(test_input))

    return attempts[:2]


def solve_task(task):
    programs = infer_programs(task)
    predictions = []
    for test_case in task["test"]:
        attempt_1, attempt_2 = select_two_attempts(task, programs, test_case["input"])
        predictions.append({"attempt_1": attempt_1, "attempt_2": attempt_2})
    return predictions, programs


def evaluate(challenges, solutions, limit=None):
    total = 0
    solved = 0
    program_counter = Counter()

    for task_index, (task_id, task) in enumerate(challenges.items()):
        if limit is not None and task_index >= limit:
            break

        predictions, programs = solve_task(task)
        if programs:
            program_counter[programs[0]["program"][0]["name"]] += 1

        for idx, prediction in enumerate(predictions):
            target = solutions[task_id][idx]
            total += 1
            if prediction["attempt_1"] == target or prediction["attempt_2"] == target:
                solved += 1

    accuracy = solved / total if total else 0
    return {"solved": solved, "total": total, "accuracy": accuracy, "program_counter": program_counter}


def make_submission(challenges):
    submission = {}
    for task_id, task in challenges.items():
        predictions, _ = solve_task(task)
        submission[task_id] = predictions
    return submission


def main():
    parser = argparse.ArgumentParser(description="Minimal symbolic ARC-AGI baseline solver.")
    parser.add_argument("--mode", choices=["evaluate", "submit", "task"], default="evaluate")
    parser.add_argument("--split", choices=["training", "evaluation", "test"], default="training")
    parser.add_argument("--task-id")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", default="submission.json")
    args = parser.parse_args()

    challenges_path = os.path.join(RAW_DATA_DIR, f"arc-agi_{args.split}_challenges.json")
    challenges = load_json(challenges_path)

    if args.mode == "task":
        if not args.task_id:
            raise SystemExit("--task-id is required for task mode")
        predictions, programs = solve_task(challenges[args.task_id])
        print(json.dumps({"task_id": args.task_id, "programs": programs, "predictions": predictions}, indent=2))
        return

    if args.mode == "evaluate":
        if args.split == "test":
            raise SystemExit("test split has no public solutions; use --mode submit")
        solutions_path = os.path.join(RAW_DATA_DIR, f"arc-agi_{args.split}_solutions.json")
        result = evaluate(challenges, load_json(solutions_path), args.limit)
        print(f"Solved: {result['solved']}/{result['total']}")
        print(f"Accuracy: {result['accuracy']:.4f}")
        print("Program hits:")
        for name, count in result["program_counter"].most_common():
            print(f"  {name}: {count}")
        return

    submission = make_submission(challenges)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(submission, handle)
    print(f"Wrote {args.output} with {len(submission)} tasks")


if __name__ == "__main__":
    main()
