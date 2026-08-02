import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

OUTPUT_DIR = "output_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

ARC_COLORS = [
    "#000000", "#0074D9", "#FF4136", "#2ECC40", "#FFDC00",
    "#AAAAAA", "#F012BE", "#FF851B", "#7FDBFF", "#870C25"
]
cmap = ListedColormap(ARC_COLORS)

# shared set of light colors for text annotation
LIGHT_COLORS = {3, 4, 5, 7, 8}

def draw_single_grid(ax, grid, title):
    grid = np.array(grid)
    rows, cols = grid.shape
    
    ax.imshow(grid, cmap=cmap, vmin=0, vmax=9)
    ax.set_xticks(np.arange(-0.5, cols, 1), [])
    ax.set_yticks(np.arange(-0.5, rows, 1), [])
    ax.grid(True, color="gray", linewidth=0.5)
    ax.set_title(title, fontsize=10)

    #  add text annotations for each cell
    for r in range(rows):
        for c in range(cols):
            val = grid[r, c]
            text_color = "black" if val in LIGHT_COLORS else "white"
            ax.text(
                c, r, str(val),
                ha='center', va='center',
                color=text_color, fontsize=8, fontweight='bold'
            )

def show_grid_pair(input_grid, output_grid, title="Grid Pair", save_path=None):
    """save_path: if provided, saves the figure to this path; otherwise, displays it."""
    fig, axes = plt.subplots(1, 2, figsize=(8, 4))
    
    draw_single_grid(axes[0], input_grid, "Input")
    draw_single_grid(axes[1], output_grid, "Output")
    
    plt.suptitle(title, fontsize=12, fontweight='bold')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=100)
        plt.close(fig)  # close the figure to free memory
    else:
        plt.show()