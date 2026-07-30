def compare_objects(input_objects, output_objects):

    input_colors = {obj["color"] for obj in input_objects}
    output_colors = {obj["color"] for obj in output_objects}

    input_count = len(input_objects)
    output_count = len(output_objects)

    comparison = {
        "input_count": input_count,
        "output_count": output_count,

        "count_changed": input_count != output_count,
        "count_difference": output_count - input_count,

        "input_colors": input_colors,
        "output_colors": output_colors,

        "added_colors": output_colors - input_colors,
        "removed_colors": input_colors - output_colors
    }

    return comparison

# ==========================================
# Detect if the object has been unchanged between input and output grids.
# ==========================================

def detect_unchanged(input_grid, output_grid):
    return input_grid == output_grid

# ==========================================
# detector for recoloring of objects in the grid.
# ==========================================

def detect_recolor(input_grid, output_grid):

    # Recolor requires the same grid size.
    if len(input_grid) != len(output_grid):
        return False

    if len(input_grid[0]) != len(output_grid[0]):
        return False

    color_mapping = {}
    color_changed = False

    for row in range(len(input_grid)):
        for col in range(len(input_grid[0])):

            input_color = input_grid[row][col]
            output_color = output_grid[row][col]

            # Record how each input color changes.
            if input_color not in color_mapping:
                color_mapping[input_color] = output_color

            # The same input color must always become the same output color.
            elif color_mapping[input_color] != output_color:
                return False

            if input_color != output_color:
                color_changed = True

    return color_changed

# ==========================================
# detect rotation and reflection of the grid.
# ==========================================

def rotate_90_clockwise(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def rotate_270_clockwise(grid):
    return [list(row) for row in zip(*grid)][::-1]


def detect_rotation(input_grid, output_grid):

    if rotate_90_clockwise(input_grid) == output_grid:
        return 90

    if rotate_180(input_grid) == output_grid:
        return 180

    if rotate_270_clockwise(input_grid) == output_grid:
        return 270

    return None

def reflect_horizontal(grid):
    # Flip top ↔ bottom
    return grid[::-1]


def reflect_vertical(grid):
    # Flip left ↔ right
    return [row[::-1] for row in grid]


def detect_reflection(input_grid, output_grid):

    if reflect_horizontal(input_grid) == output_grid:
        return "horizontal"

    if reflect_vertical(input_grid) == output_grid:
        return "vertical"

    return None

# ==========================================
# Crop
# ==========================================

def detect_crop(input_grid, output_grid):
    input_height = len(input_grid)
    input_width = len(input_grid[0])

    output_height = len(output_grid)
    output_width = len(output_grid[0])

    if output_height > input_height or output_width > input_width:
        return None

    for top in range(input_height - output_height + 1):
        for left in range(input_width - output_width + 1):

            cropped = [
                row[left:left + output_width]
                for row in input_grid[top:top + output_height]
            ]

            if cropped == output_grid:
                return {
                    "top": top,
                    "left": left,
                    "height": output_height,
                    "width": output_width
                }

    return None


# ==========================================
# Scale up each cell
# ==========================================

def detect_scale_up(input_grid, output_grid):
    input_height = len(input_grid)
    input_width = len(input_grid[0])

    output_height = len(output_grid)
    output_width = len(output_grid[0])

    if output_height % input_height != 0:
        return None

    if output_width % input_width != 0:
        return None

    row_scale = output_height // input_height
    column_scale = output_width // input_width

    # Scale-up must actually make the grid larger.
    if row_scale == 1 and column_scale == 1:
        return None

    for row in range(output_height):
        for col in range(output_width):

            expected_color = input_grid[
                row // row_scale
            ][
                col // column_scale
            ]

            if output_grid[row][col] != expected_color:
                return None

    return {
        "row_scale": row_scale,
        "column_scale": column_scale
    }


# ==========================================
# Repeat the whole grid like tiles
# ==========================================

def detect_tile_repeat(input_grid, output_grid):
    input_height = len(input_grid)
    input_width = len(input_grid[0])

    output_height = len(output_grid)
    output_width = len(output_grid[0])

    if output_height % input_height != 0:
        return None

    if output_width % input_width != 0:
        return None

    row_repeats = output_height // input_height
    column_repeats = output_width // input_width

    if row_repeats == 1 and column_repeats == 1:
        return None

    for row in range(output_height):
        for col in range(output_width):

            expected_color = input_grid[
                row % input_height
            ][
                col % input_width
            ]

            if output_grid[row][col] != expected_color:
                return None

    return {
        "row_repeats": row_repeats,
        "column_repeats": column_repeats
    }


# ==========================================
# Simple translation inside the same grid
# ==========================================

def shift_grid(grid, row_shift, column_shift, background=0):
    height = len(grid)
    width = len(grid[0])

    shifted = [
        [background for _ in range(width)]
        for _ in range(height)
    ]

    for row in range(height):
        for col in range(width):

            if grid[row][col] == background:
                continue

            new_row = row + row_shift
            new_col = col + column_shift

            if 0 <= new_row < height and 0 <= new_col < width:
                shifted[new_row][new_col] = grid[row][col]

    return shifted


def detect_translation(input_grid, output_grid):
    if len(input_grid) != len(output_grid):
        return None

    if len(input_grid[0]) != len(output_grid[0]):
        return None

    height = len(input_grid)
    width = len(input_grid[0])

    for row_shift in range(-(height - 1), height):
        for column_shift in range(-(width - 1), width):

            if row_shift == 0 and column_shift == 0:
                continue

            shifted = shift_grid(
                input_grid,
                row_shift,
                column_shift
            )

            if shifted == output_grid:
                return {
                    "row_shift": row_shift,
                    "column_shift": column_shift
                }

    return None

def detect_all_rules(input_grid, output_grid):

    results = {
        "unchanged": detect_unchanged(
            input_grid,
            output_grid
        ),

        "recolor": detect_recolor(
            input_grid,
            output_grid
        ),

        "rotation": detect_rotation(
            input_grid,
            output_grid
        ),

        "reflection": detect_reflection(
            input_grid,
            output_grid
        ),

        "crop": detect_crop(
            input_grid,
            output_grid
        ),

        "scale_up": detect_scale_up(
            input_grid,
            output_grid
        ),

        "tile_repeat": detect_tile_repeat(
            input_grid,
            output_grid
        ),

        "translation": detect_translation(
            input_grid,
            output_grid
        )
    }

    return results