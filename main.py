import os
import json
import pandas as pd  

# ==========================================
# Imports from your custom modules
# ==========================================
# 1. Visualization functions should come from visualizer.py
from visualizer import show_grid_pair 

# 2. Object extraction functions should come from features.py
from features import extract_all_objects 

# 3. Rule detection functions (detect_all_rules internally calls all the specific detectors)
from rule_detector import compare_objects, detect_all_rules

# ==========================================
# Configuration Settings
# ==========================================
SAVE_IMAGES = True       # Set to False if you only want the CSV report (much faster)
MAX_TASKS = 1200         # Maximum number of tasks to process (set to None for all)
OUTPUT_DIR = "output_images"

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define paths to the JSON datasets
challenges_path = os.path.join("Raw Data", "arc-agi_training_challenges.json")

# Load the dataset
with open(challenges_path, "r") as challenge_file:
    challenges = json.load(challenge_file)

print("=== STARTING ARC DATA ANALYSIS ===")

# List to hold dictionary records for the final DataFrame
analysis_records = []

# ==========================================
# Main Processing Loop
# ==========================================
for task_index, (task_id, task) in enumerate(challenges.items()):

    # Stop if we reach the specified maximum number of tasks
    if MAX_TASKS is not None and task_index >= MAX_TASKS:
        break

    # Print progress every 50 tasks
    if (task_index + 1) % 50 == 0:
        print(f"Processed {task_index + 1} tasks...")

    # Iterate over every training example within the task
    for example_index, example in enumerate(task["train"]):

        input_grid = example["input"]
        output_grid = example["output"]

        # 1. Feature Extraction & Comparison
        input_objects = extract_all_objects(input_grid)
        output_objects = extract_all_objects(output_grid)
        facts = compare_objects(input_objects, output_objects)
        
        # 2. Rule Detection (Calls the wrapper function that runs all detectors)
        detected_rules = detect_all_rules(input_grid, output_grid)

        # Collect rules that evaluated to True or returned a valid dictionary (ignore False/None)
        active_rules = [
            rule for rule, result in detected_rules.items() 
            if result not in (False, None)
        ]

        # 3. Package the data into a dictionary for CSV export
        record = {
            "task_id": task_id,
            "example_id": example_index + 1,
            "input_shape": f"{len(input_grid)}x{len(input_grid[0])}",
            "output_shape": f"{len(output_grid)}x{len(output_grid[0])}",
            "shape_changed": (len(input_grid) != len(output_grid)) or (len(input_grid[0]) != len(output_grid[0])),
            "input_obj_count": len(input_objects),
            "output_obj_count": len(output_objects),
            "obj_count_changed": facts["count_changed"],
            
            # Convert the list of triggered rules into a readable string
            "detected_rules": ", ".join(active_rules) if active_rules else "None",
            "rule_count": len(active_rules),
            
            # Specific rule booleans/flags for easy filtering in Excel/Pandas
            "recolor": detected_rules.get("recolor", False) != False,
            "rotation": detected_rules.get("rotation", None),
            "reflection": detected_rules.get("reflection", None),
            "crop": detected_rules.get("crop", None) is not None,
            "scale_up": detected_rules.get("scale_up", None) is not None,
            "translation": detected_rules.get("translation", None) is not None
        }
        
        analysis_records.append(record)

        # 4. Image Generation (Side-by-side comparison)
        if SAVE_IMAGES:
            img_path = os.path.join(OUTPUT_DIR, f"task_{task_id}_ex_{example_index + 1}.png")
            show_grid_pair(
                input_grid, 
                output_grid, 
                title=f"Task {task_id} - Ex {example_index + 1}", 
                save_path=img_path
            )

# ==========================================
# Exporting Data to CSV
# ==========================================
df = pd.DataFrame(analysis_records)
csv_save_path = "arc_rule_analysis.csv"

# utf-8-sig ensures Excel reads the file correctly without encoding issues
df.to_csv(csv_save_path, index=False, encoding="utf-8-sig")

# Print Summary
print("\n==========================================")
print(f" Analysis Complete!")
print(f" Total records saved to CSV: {len(df)}")
print(f" CSV Report generated at: {csv_save_path}")
if SAVE_IMAGES:
    print(f" Visualizations saved in: ./{OUTPUT_DIR}/")
print("==========================================\n")

# Display a quick statistical summary of the most frequently detected rules
print("--- Top 10 Detected Rules Frequency ---")
print(df["detected_rules"].value_counts().head(10))