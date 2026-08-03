# ARC-AGI-2 Baseline

Minimal symbolic baseline and data-analysis tools for ARC Prize 2026 ARC-AGI-2.

## Setup

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run The Symbolic Solver

Evaluate a small training subset:

```bash
python solver.py --mode evaluate --split training --limit 100
```

Evaluate the full public training split:

```bash
python solver.py --mode evaluate --split training
```

Inspect one task:

```bash
python solver.py --mode task --split training --task-id 00576224
```

Generate a Kaggle-style submission file:

```bash
python solver.py --mode submit --split test --output baseline_submission.json
```

## Run The Existing Rule Analysis

`main.py` reads the training challenges, detects simple rules, writes
`arc_rule_analysis.csv`, and optionally saves visualizations to `output_images/`.

```bash
python main.py
```

For faster runs, edit `SAVE_IMAGES` and `MAX_TASKS` near the top of `main.py`.
