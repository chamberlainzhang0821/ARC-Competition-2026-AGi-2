import os
import json

# ==========================================
# Path Configuration
# ==========================================
# locate the project root directory and set the data directory path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "Raw Data")

def load_arc_data(split="training"):
    """
    Load and merge ARC tasks and solutions.
    :param split: 'training' or 'evaluation'
    :return: A dictionary with task_id as keys and complete train/test data as values.
    """
    challenges_file = os.path.join(DATA_DIR, f"arc-agi_{split}_challenges.json")
    solutions_file = os.path.join(DATA_DIR, f"arc-agi_{split}_solutions.json")
    
    # 1. load (Challenges)
    if not os.path.exists(challenges_file):
        print(f"Error: File not found {challenges_file}")
        return {}
        
    with open(challenges_file, 'r') as f:
        challenges = json.load(f)
        
    # 2. load solutions (Solutions)
    solutions = {}
    if os.path.exists(solutions_file):
        with open(solutions_file, 'r') as f:
            solutions = json.load(f)
    else:
        print(f"Warning: File not found {solutions_file}, Test set will have no ground truth answers.")
            
    # 3. merge data
    merged_data = {}
    for task_id, task_data in challenges.items():
        # extract Train data (directly copy)
        merged_task = {"train": task_data.get("train", [])}
        
        # extract Test data and attach corresponding Solution
        test_examples = task_data.get("test", [])
        task_solutions = solutions.get(task_id, [])
        
        merged_test = []
        for i, test_input_dict in enumerate(test_examples):
            merged_example = {"input": test_input_dict["input"]}
            # if the solutions file has the corresponding output matrix, attach it
            if i < len(task_solutions):
                merged_example["output"] = task_solutions[i]
            merged_test.append(merged_example)
            
        merged_task["test"] = merged_test
        merged_data[task_id] = merged_task
        
    return merged_data

# ==========================================
# Testing the Data Loader
# ==========================================
if __name__ == "__main__":
    print(f"Looking for data in: {DATA_DIR}")
    
    # Test loading training data
    train_tasks = load_arc_data("training")
    task_ids = list(train_tasks.keys())
    
    if task_ids:
        print(f"\n✅ Successfully loaded {len(task_ids)} training tasks!")
        
        # Randomly check the first task to see its structure
        sample_id = task_ids[0]
        sample_task = train_tasks[sample_id]
        print(f"\n--- Task {sample_id} Structure Preview ---")
        print(f"Train Examples: {len(sample_task['train'])}")
        print(f"Test Examples: {len(sample_task['test'])}")
        
        # Check if Test data has successfully attached output
        if "output" in sample_task["test"][0]:
            print("✅ Test set answers (Solutions) attached successfully!")
        else:
            print("❌ Test set answers (Solutions) missing!")
