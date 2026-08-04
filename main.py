import os
import json
import pandas as pd
import traceback
from tqdm import tqdm  

# ==========================================
# Imports from your custom modules
# ==========================================
# 1. Visualization functions should come from visualizer.py
from visualizer import show_grid_pair 

# 2. Object extraction functions should come from features.py
from features import extract_all_objects 

# 3. Rule detection functions 
from rule_detector import compare_objects, detect_all_rules

# ==========================================
# Configuration Settings
# ==========================================
SAVE_IMAGES = True       # Set to False if you only want the CSV report (much faster)
MAX_TASKS = 1200         # Maximum number of tasks to process (set to None for all)
OUTPUT_DIR = "output_images_evaluation"  
CSV_OUTPUT_DIR = "output_csv_evaluation"
DATASET_PATH = os.path.join("Raw Data", "arc-agi_evaluation_challenges.json")


def main():
    # Ensure the output directories exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CSV_OUTPUT_DIR, exist_ok=True)

    # Check if dataset exists
    if not os.path.exists(DATASET_PATH):
        print(f"[Error] Dataset not found at: {DATASET_PATH}")
        print("Please ensure the 'Raw Data' folder exists and contains the JSON file.")
        return

    # Load the dataset
    print("Loading dataset...")
    with open(DATASET_PATH, "r") as challenge_file:
        challenges = json.load(challenge_file)

    print("\n=== STARTING ARC DATA ANALYSIS ===")
    
    analysis_records = []
    
    # Determine the number of tasks to process for tqdm
    total_tasks = len(challenges)
    if MAX_TASKS is not None:
        total_tasks = min(total_tasks, MAX_TASKS)

    # Convert dict items to a list and slice it if MAX_TASKS is set
    task_items = list(challenges.items())[:total_tasks]

    # ==========================================
    # Main Processing Loop with Progress Bar
    # ==========================================
    for task_id, task in tqdm(task_items, desc="Processing Tasks", unit="task"):
        
        for example_index, example in enumerate(task.get("train", [])):
            input_grid = example["input"]
            output_grid = example["output"]
            
            try:
                # 1. Feature Extraction & Comparison
                input_objects = extract_all_objects(input_grid)
                output_objects = extract_all_objects(output_grid)
                facts = compare_objects(input_objects, output_objects)
                
                # 2. Rule Detection 
                detected_rules = detect_all_rules(input_grid, output_grid)

                # Collect active rules
                active_rules = [
                    rule for rule, result in detected_rules.items() 
                    if result not in (False, None)
                ]

                # 3. Package data
                record = {
                    "task_id": task_id,
                    "example_id": example_index + 1,
                    "input_shape": f"{len(input_grid)}x{len(input_grid[0])}",
                    "output_shape": f"{len(output_grid)}x{len(output_grid[0])}",
                    "shape_changed": (len(input_grid) != len(output_grid)) or (len(input_grid[0]) != len(output_grid[0])),
                    "input_obj_count": len(input_objects),
                    "output_obj_count": len(output_objects),
                    "obj_count_changed": facts.get("count_changed", False),
                    
                    "detected_rules": ", ".join(active_rules) if active_rules else "None",
                    "rule_count": len(active_rules),
                    
                    "recolor": detected_rules.get("recolor", False) != False,
                    "rotation": detected_rules.get("rotation", None),
                    "reflection": detected_rules.get("reflection", None),
                    "crop": detected_rules.get("crop", None) is not None,
                    "scale_up": detected_rules.get("scale_up", None) is not None,
                    "translation": detected_rules.get("translation", None) is not None,
                    
                    "color_substitution": detected_rules.get("color_substitution", None) is not None,
                    "flood_fill": detected_rules.get("flood_fill", None) is not None,
                    "gravity": detected_rules.get("gravity", None) is not None,
                    "line_drawing": detected_rules.get("line_drawing", None) is not None
                }
                
                analysis_records.append(record)

                # 4. Image Generation
                if SAVE_IMAGES:
                    img_path = os.path.join(OUTPUT_DIR, f"task_{task_id}_ex_{example_index + 1}.png")
                    show_grid_pair(
                        input_grid, 
                        output_grid, 
                        title=f"Task {task_id} - Ex {example_index + 1}", 
                        save_path=img_path
                    )

            except Exception as e:
                # Catch any errors from custom rule detectors to prevent stopping the whole script
                tqdm.write(f"\n[Warning] Error processing Task {task_id} Example {example_index + 1}: {e}")
                # Optional: Uncomment below to see full error tracebacks during debugging
                # tqdm.write(traceback.format_exc())

    # ==========================================
    # Exporting Data to CSV
    # ==========================================
    if not analysis_records:
        print("\n[Warning] No records were successfully processed. CSV will not be saved.")
        return

    df = pd.DataFrame(analysis_records)
    csv_save_path = os.path.join(CSV_OUTPUT_DIR, "arc_rule_analysis_evaluation.csv")

    df.to_csv(csv_save_path, index=False, encoding="utf-8-sig")

    # Print Summary
    print("\n==========================================")
    print(" Analysis Complete!")
    print(f" Total records saved to CSV: {len(df)}")
    print(f" CSV Report generated at: {csv_save_path}")
    if SAVE_IMAGES:
        print(f" Visualizations saved in: ./{OUTPUT_DIR}/")
    print("==========================================\n")

    print("--- Top 10 Detected Rules Frequency ---")
    print(df["detected_rules"].value_counts().head(10))

if __name__ == "__main__":
    main()
