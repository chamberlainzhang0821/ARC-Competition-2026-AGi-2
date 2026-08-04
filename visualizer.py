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

def get_diff_grid(input_grid, output_grid):
    """
    计算输入和输出矩阵的差集。
    只要形状一样，就直接把不一样的格子提取出来，一样的地方全变成黑色 (0)
    """
    inp = np.array(input_grid)
    out = np.array(output_grid)
    diff = np.where(inp != out, out, 0)
    return diff

def draw_single_grid(ax, grid, title):
    grid = np.array(grid)
    rows, cols = grid.shape
    
    ax.imshow(grid, cmap=cmap, vmin=0, vmax=9)
    ax.set_xticks(np.arange(-0.5, cols, 1), [])
    ax.set_yticks(np.arange(-0.5, rows, 1), [])
    ax.grid(True, color="gray", linewidth=0.5)
    ax.set_title(title, fontsize=10)

    # add text annotations for each cell
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
    inp = np.array(input_grid)
    out = np.array(output_grid)
    
    # 如果形状相同，生成 1x3 的图（加入 Diff）
    if inp.shape == out.shape:
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        draw_single_grid(axes[0], inp, "Input")
        draw_single_grid(axes[1], out, "Output")
        
        diff = get_diff_grid(inp, out)
        draw_single_grid(axes[2], diff, "Diff (Changes)")
        
    # 如果形状不同（例如裁剪、放大），只能生成 1x2 的图
    else:
        fig, axes = plt.subplots(1, 2, figsize=(8, 4))
        draw_single_grid(axes[0], inp, "Input")
        draw_single_grid(axes[1], out, "Output")
    
    plt.suptitle(title, fontsize=12, fontweight='bold')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=100)
        plt.close(fig)  # close the figure to free memory
    else:
        plt.show()
