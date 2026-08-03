
def copy_grid(grid):
    return [row[:] for row in grid]


def validate_grid(grid):
    if not isinstance(grid, list) or not grid:
        return False

    width = None
    for row in grid:
        if not isinstance(row, list) or not row:
            return False
        if width is None:
            width = len(row)
        elif len(row) != width:
            return False
        for value in row:
            if not isinstance(value, int) or value < 0 or value > 9:
                return False

    return 1 <= len(grid) <= 30 and 1 <= width <= 30


def identity(grid):
    return copy_grid(grid)


def rotate(grid, angle):
    if angle == 90:
        return [list(row) for row in zip(*grid[::-1])]
    if angle == 180:
        return [row[::-1] for row in grid[::-1]]
    if angle == 270:
        return [list(row) for row in zip(*grid)][::-1]
    if angle == 0:
        return copy_grid(grid)
    raise ValueError(f"unsupported rotate angle: {angle}")


def flip(grid, axis):
    if axis == "horizontal":
        return grid[::-1]
    if axis == "vertical":
        return [row[::-1] for row in grid]
    raise ValueError(f"unsupported flip axis: {axis}")


def translate(grid, row_shift, col_shift, fill_color=0):
    height = len(grid)
    width = len(grid[0])
    output = [[fill_color for _ in range(width)] for _ in range(height)]

    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == fill_color:
                continue
            new_row = row + row_shift
            new_col = col + col_shift
            if 0 <= new_row < height and 0 <= new_col < width:
                output[new_row][new_col] = value

    return output


def crop(grid, top, left, height, width):
    if height <= 0 or width <= 0:
        raise ValueError("crop height and width must be positive")
    if top < 0 or left < 0:
        raise ValueError("crop top and left must be non-negative")
    if top + height > len(grid) or left + width > len(grid[0]):
        raise ValueError("crop exceeds grid bounds")
    return [row[left:left + width] for row in grid[top:top + height]]


def crop_non_background(grid, background=0):
    cells = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] != background
    ]
    if not cells:
        raise ValueError("cannot crop an empty foreground")

    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return crop(grid, min(rows), min(cols), max(rows) - min(rows) + 1, max(cols) - min(cols) + 1)


def replace_color(grid, source, target):
    return [[target if value == source else value for value in row] for row in grid]


def replace_colors(grid, mapping):
    normalized = {int(source): int(target) for source, target in mapping.items()}
    return [[normalized.get(value, value) for value in row] for row in grid]


def scale(grid, row_scale=1, col_scale=None, factor=None):
    if factor is not None:
        row_scale = factor
        col_scale = factor
    if col_scale is None:
        col_scale = row_scale
    if row_scale <= 0 or col_scale <= 0:
        raise ValueError("scale factors must be positive")

    output = []
    for row in grid:
        scaled_row = []
        for value in row:
            scaled_row.extend([value] * col_scale)
        for _ in range(row_scale):
            output.append(scaled_row[:])

    if len(output) > 30 or len(output[0]) > 30:
        raise ValueError("scaled grid exceeds 30x30")
    return output


def tile(grid, rows=1, cols=1):
    if rows <= 0 or cols <= 0:
        raise ValueError("tile repeats must be positive")
    output = []
    for _ in range(rows):
        for row in grid:
            output.append(row * cols)

    if len(output) > 30 or len(output[0]) > 30:
        raise ValueError("tiled grid exceeds 30x30")
    return output


def apply_operation(grid, operation):
    name = operation["name"]
    params = operation.get("parameters", {})

    if name == "identity":
        return identity(grid)
    if name == "rotate":
        return rotate(grid, params["angle"])
    if name == "flip":
        return flip(grid, params["axis"])
    if name == "translate":
        return translate(
            grid,
            params["row_shift"],
            params["col_shift"],
            params.get("fill_color", 0),
        )
    if name == "crop":
        return crop(grid, params["top"], params["left"], params["height"], params["width"])
    if name == "crop_non_background":
        return crop_non_background(grid, params.get("background", 0))
    if name == "replace_color":
        return replace_color(grid, params["source"], params["target"])
    if name == "replace_colors":
        return replace_colors(grid, params["mapping"])
    if name == "scale":
        return scale(
            grid,
            params.get("row_scale", 1),
            params.get("col_scale"),
            params.get("factor"),
        )
    if name == "tile":
        return tile(grid, params.get("rows", 1), params.get("cols", 1))

    raise ValueError(f"unsupported operation: {name}")


def execute_program(grid, operations):
    output = copy_grid(grid)
    for operation in operations:
        output = apply_operation(output, operation)
        if not validate_grid(output):
            raise ValueError("operation produced an invalid grid")
    return output
