import numpy as np
from scipy.ndimage import label
from scipy.stats import entropy

# ==========================================
# 1. Macro Features (Statistical & Topological)
# ==========================================

def get_color_entropy(grid):
    """
    Calculate the Shannon entropy of the color distribution.
    A higher value means more colors are evenly distributed.
    """
    grid = np.array(grid)
    # Count the frequency of each color present in the grid
    _, counts = np.unique(grid, return_counts=True)
    # Calculate entropy using base 2
    return float(entropy(counts, base=2))

def get_connected_components(grid):
    """
    Count the total number of distinct, contiguous non-zero color blocks (4-connectivity).
    """
    grid = np.array(grid)
    total_components = 0
    colors = np.unique(grid)
    
    for color in colors:
        # Ignore the background color (0)
        if color == 0:
            continue
            
        # Create a binary mask for the current color
        mask = (grid == color).astype(int)
        
        # scipy.ndimage.label groups adjacent identical pixels into single components
        _, num_features = label(mask)
        total_components += num_features
        
    return total_components

def get_symmetry_score(grid):
    """
    Check for horizontal and vertical symmetry of the entire grid.
    Returns 0 (no symmetry), 1 (one axis of symmetry), or 2 (both axes).
    """
    grid = np.array(grid)
    
    # Check if the grid equals its vertically flipped self
    horizontal_sym = np.array_equal(grid, np.flipud(grid))
    
    # Check if the grid equals its horizontally flipped self
    vertical_sym = np.array_equal(grid, np.fliplr(grid))
    
    score = 0
    if horizontal_sym:
        score += 1
    if vertical_sym:
        score += 1
        
    return score

def get_border_touch_ratio(grid):
    """
    Calculate the percentage of non-zero pixels that touch the outer boundary of the grid.
    """
    grid = np.array(grid)
    rows, cols = grid.shape
    
    # Create a boolean mask for all foreground (non-zero) pixels
    non_zero = grid > 0
    total_non_zero = np.sum(non_zero)
    
    if total_non_zero == 0:
        return 0.0
        
    # Sum the non-zero pixels exactly on the four borders
    border_pixels = 0
    border_pixels += np.sum(non_zero[0, :])                 # Top row
    border_pixels += np.sum(non_zero[rows-1, :])            # Bottom row
    # Avoid double-counting the corners by slicing the columns
    if rows > 2:
        border_pixels += np.sum(non_zero[1:rows-1, 0])      # Left column (excluding corners)
        border_pixels += np.sum(non_zero[1:rows-1, cols-1]) # Right column (excluding corners)
        
    return float(border_pixels / total_non_zero)

def extract_macro_features(grid):
    """
    Wrapper function: receives a 2D matrix and returns a dictionary of macro-features.
    """
    return {
        "color_entropy": get_color_entropy(grid),
        "num_components": get_connected_components(grid),
        "symmetry_score": get_symmetry_score(grid),
        "border_ratio": get_border_touch_ratio(grid)
    }


# ==========================================
# 2. Micro Features (Object Extraction)
# ==========================================

def get_colors(grid):
    grid = np.array(grid)
    colors = np.unique(grid)
    return colors

def get_color_positions(grid, color):
    grid = np.array(grid)
    positions = np.argwhere(grid == color)
    return positions

def find_objects(grid, color):
    """
    Find all isolated contiguous objects of a specific color using Depth-First Search (DFS).
    """
    grid = np.array(grid)
    visited = set()
    objects = []
    rows, cols = grid.shape

    for row in range(rows):
        for col in range(cols):
            if grid[row, col] == color and (row, col) not in visited:
                object_cells = []
                stack = [(row, col)]

                # Traverse neighboring cells of the same color
                while stack:
                    current_row, current_col = stack.pop()
                    if (current_row, current_col) in visited:
                        continue

                    visited.add((current_row, current_col))
                    object_cells.append((current_row, current_col))

                    # 4-directional neighbors
                    neighbors = [
                        (current_row - 1, current_col),
                        (current_row + 1, current_col),
                        (current_row, current_col - 1),
                        (current_row, current_col + 1),
                    ]

                    for next_row, next_col in neighbors:
                        inside_grid = (0 <= next_row < rows and 0 <= next_col < cols)
                        if inside_grid and grid[next_row, next_col] == color and (next_row, next_col) not in visited:
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
    """
    Extract detailed features (size, bounding box, dimensions) for every object in the grid.
    """
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
