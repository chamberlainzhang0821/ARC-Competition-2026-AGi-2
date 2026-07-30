import json

from visualizer import show_grid
from features import extract_all_objects
from rule_detector import compare_objects, detect_all_rules

SHOW_GRID = True
SHOW_OBJECTS = False

with open("arcagi_training_Challenges.json","r") as challenge_file:
    challenges = json.load(challenge_file)

with open("arcagi_training_solutions.json","r") as solution_file:
    solutions = json.load(solution_file)

print("=== NEW RUN ===")

for task_index, (task_id, task) in enumerate(challenges.items()):

    if task_index >= 10:
        break

    print("\n==============================")
    print("Task ID:", task_id)
    print("==============================")

    for example_index, example in enumerate(task["train"]):

        print(f"\n===== Training Example {example_index + 1} =====")

        input_grid = example["input"]
        output_grid = example["output"]

        input_objects = extract_all_objects(input_grid)
        output_objects = extract_all_objects(output_grid)

        # Show ARC grids while debugging.
        # Turn OFF when testing algorithms or running many tasks.
        if SHOW_GRID:
            show_grid(input_grid, "Training Input")
            show_grid(output_grid, "Training Output")

        if SHOW_OBJECTS:
            print("Input objects:")
            for obj in input_objects:
                print(obj)

            print("Output objects:")
            for obj in output_objects:
                print(obj)


        input_height = len(input_grid)
        input_width = len(input_grid[0])

        output_height = len(output_grid)
        output_width = len(output_grid[0])

        print("Input shape:", input_height, "x", input_width)
        print("Output shape:", output_height, "x", output_width)

        print("Input object count:", len(input_objects))
        print("Output object count:", len(output_objects))

        facts = compare_objects(input_objects, output_objects)
        print("Facts:", facts)
        detected_rules = detect_all_rules(
        input_grid,
        output_grid
    )
        print("Detected rules:")

        for rule_name, result in detected_rules.items():
            if result not in (False, None):
                print(rule_name, ":", result)

        print("--------------------")