import numpy as np

def get_colors(grid):
    grid = np.array(grid)
    colors = np.unique(grid)
    return colors

def get_color_positions(grid, color):
    grid = np.array(grid)
    positions = np.argwhere(grid == color)
    return positions

def find_objects(grid, color):
    grid = np.array(grid)
    visited = set()
    objects = []
    rows, cols = grid.shape

    for row in range(rows):
        for col in range(cols):
            if grid[row, col] == color and (row, col) not in visited:
                object_cells = []
                stack = [(row, col)]

                while stack:
                    current_row, current_col = stack.pop()
                    if (current_row, current_col) in visited:
                        continue

                    visited.add((current_row, current_col))
                    object_cells.append((current_row, current_col))

                    neighbors = [
                        (current_row - 1, current_col),
                        (current_row + 1, current_col),
                        (current_row, current_col - 1),
                        (current_row, current_col + 1),
                    ]

                    for next_row, next_col in neighbors:
                        inside_grid = (0 <= next_row < rows and 0 <= next_col < cols)
                        if (inside_grid and grid[next_row, next_col] == color and (next_row, next_col) not in visited):
                            stack.append((next_row, next_col))

                objects.append(object_cells)

    return objects

def get_object_size(object_cells):
    return len(object_cells)

def get_bounding_box(object_cells):
    rows = [row for row, col in object_cells]
    cols = [col for row, col in object_cells]
    top = min(rows)
    bottom = max(rows)
    left = min(cols)
    right = max(cols)
    return top, bottom, left, right

def get_object_dimensions(object_cells):
    top, bottom, left, right = get_bounding_box(object_cells)
    height = bottom - top + 1
    width = right - left + 1
    return height, width

def get_object_features(object_cells, color):
    size = get_object_size(object_cells)
    bounding_box = get_bounding_box(object_cells)
    height, width = get_object_dimensions(object_cells)

    return {
        "color": int(color),
        "size": size,
        "bounding_box": bounding_box,
        "height": height,
        "width": width
    }

def extract_all_objects(grid):
    all_objects = []
    colors = get_colors(grid)

    for color in colors:
        # Ignore background color 0
        if color == 0:
            continue
        objects = find_objects(grid, color)
        for obj in objects:
            features = get_object_features(obj, color)
            all_objects.append(features)

    return all_objects
