import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

ARC_COLORS = [
    "#000000",  # 0 black
    "#0074D9",  # 1 blue
    "#FF4136",  # 2 red
    "#2ECC40",  # 3 green
    "#FFDC00",  # 4 yellow
    "#AAAAAA",  # 5 gray
    "#F012BE",  # 6 magenta
    "#FF851B",  # 7 orange
    "#7FDBFF",  # 8 azure
    "#870C25",  # 9 maroon/brown
]

cmap = ListedColormap(ARC_COLORS)

def show_grid(grid, title = "Grid"):
    grid = np.array(grid)

    plt.figure(figsize=(5, 5))

    plt.imshow(
        grid,
        cmap=cmap,
        vmin=0,
        vmax=9
    )

    plt.xticks(
        np.arange(-0.5, grid.shape[1], 1),
        []
    )

    plt.yticks(
        np.arange(-0.5, grid.shape[0], 1),
        []
    )

    plt.grid()
    plt.title(title)
    plt.show()