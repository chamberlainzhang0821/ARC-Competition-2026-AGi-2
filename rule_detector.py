import collections

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
# 1. Unchanged & Global Recolor
# ==========================================

def detect_unchanged(input_grid, output_grid):
    return input_grid == output_grid

def detect_recolor(input_grid, output_grid):
    if len(input_grid) != len(output_grid) or len(input_grid[0]) != len(output_grid[0]):
        return False
        
    color_mapping = {}
    color_changed = False

    for row in range(len(input_grid)):
        for col in range(len(input_grid[0])):
            input_color = input_grid[row][col]
            output_color = output_grid[row][col]

            if input_color not in color_mapping:
                color_mapping[input_color] = output_color
            elif color_mapping[input_color] != output_color:
                return False

            if input_color != output_color:
                color_changed = True

    return color_changed

# ==========================================
# 2. Geometry: Rotation, Reflection, Crop, Scale, Tile, Translation
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
    return grid[::-1]

def reflect_vertical(grid):
    return [row[::-1] for row in grid]

def detect_reflection(input_grid, output_grid):
    if reflect_horizontal(input_grid) == output_grid:
        return "horizontal"
    if reflect_vertical(input_grid) == output_grid:
        return "vertical"
    return None

def detect_crop(input_grid, output_grid):
    input_height, input_width = len(input_grid), len(input_grid[0])
    output_height, output_width = len(output_grid), len(output_grid[0])

    if output_height > input_height or output_width > input_width:
        return None

    for top in range(input_height - output_height + 1):
        for left in range(input_width - output_width + 1):
            cropped = [
                row[left:left + output_width]
                for row in input_grid[top:top + output_height]
            ]
            if cropped == output_grid:
                return {"top": top, "left": left, "height": output_height, "width": output_width}
    return None

def detect_scale_up(input_grid, output_grid):
    input_height, input_width = len(input_grid), len(input_grid[0])
    output_height, output_width = len(output_grid), len(output_grid[0])

    if output_height % input_height != 0 or output_width % input_width != 0:
        return None

    row_scale = output_height // input_height
    column_scale = output_width // input_width

    if row_scale == 1 and column_scale == 1:
        return None

    for row in range(output_height):
        for col in range(output_width):
            expected_color = input_grid[row // row_scale][col // column_scale]
            if output_grid[row][col] != expected_color:
                return None
    return {"row_scale": row_scale, "column_scale": column_scale}

def detect_tile_repeat(input_grid, output_grid):
    input_height, input_width = len(input_grid), len(input_grid[0])
    output_height, output_width = len(output_grid), len(output_grid[0])

    if output_height % input_height != 0 or output_width % input_width != 0:
        return None

    row_repeats = output_height // input_height
    column_repeats = output_width // input_width

    if row_repeats == 1 and column_repeats == 1:
        return None

    for row in range(output_height):
        for col in range(output_width):
            expected_color = input_grid[row % input_height][col % input_width]
            if output_grid[row][col] != expected_color:
                return None
    return {"row_repeats": row_repeats, "column_repeats": column_repeats}

def shift_grid(grid, row_shift, column_shift, background=0):
    height, width = len(grid), len(grid[0])
    shifted = [[background for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == background:
                continue
            new_row, new_col = row + row_shift, col + column_shift
            if 0 <= new_row < height and 0 <= new_col < width:
                shifted[new_row][new_col] = grid[row][col]
    return shifted

def detect_translation(input_grid, output_grid):
    if len(input_grid) != len(output_grid) or len(input_grid[0]) != len(output_grid[0]):
        return None
    height, width = len(input_grid), len(input_grid[0])
    
    for row_shift in range(-(height - 1), height):
        for column_shift in range(-(width - 1), width):
            if row_shift == 0 and column_shift == 0:
                continue
            if shift_grid(input_grid, row_shift, column_shift) == output_grid:
                return {"row_shift": row_shift, "column_shift": column_shift}
    return None


# ==========================================
# 🌟 NEW: ARC Core Primitives (物理引擎机制)
# ==========================================

def detect_color_substitution(input_grid, output_grid):
    """
    机制 4: 密码本机制。不仅返回 True/False，而是返回具体的颜色转换字典 color_map。
    """
    if len(input_grid) != len(output_grid) or len(input_grid[0]) != len(output_grid[0]):
        return None

    color_map = {}
    is_changed = False

    for r in range(len(input_grid)):
        for c in range(len(input_grid[0])):
            i_color = input_grid[r][c]
            o_color = output_grid[r][c]
            
            if i_color not in color_map:
                color_map[i_color] = o_color
            elif color_map[i_color] != o_color:
                return None # 颜色映射冲突，不是单纯的替换规律
                
            if i_color != o_color:
                is_changed = True

    if is_changed:
        # 只提取真正发生了改变的颜色映射 (e.g., {5: 1, 2: 6})
        real_changes = {k: v for k, v in color_map.items() if k != v}
        return {"mapping": real_changes}
    return None

def detect_flood_fill(input_grid, output_grid):
    """
    机制 2: 拓扑填色机制。利用 BFS 寻找被包围的闭合区域 (enclosed areas)，检查它们是否被填充了颜色。
    """
    if len(input_grid) != len(output_grid) or len(input_grid[0]) != len(output_grid[0]):
        return None

    height, width = len(input_grid), len(input_grid[0])
    visited = set()
    enclosed_pixels = []

    # 1. 找到所有被完全包围的 0 (背景色) 区域
    for r in range(height):
        for c in range(width):
            if input_grid[r][c] == 0 and (r, c) not in visited:
                q = collections.deque([(r, c)])
                visited.add((r, c))
                component = []
                touches_boundary = False
                
                while q:
                    curr_r, curr_c = q.popleft()
                    component.append((curr_r, curr_c))
                    
                    if curr_r == 0 or curr_r == height - 1 or curr_c == 0 or curr_c == width - 1:
                        touches_boundary = True

                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < height and 0 <= nc < width:
                            if input_grid[nr][nc] == 0 and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                q.append((nr, nc))
                                
                if not touches_boundary:
                    enclosed_pixels.extend(component)

    if not enclosed_pixels:
        return None

    # 2. 检查输出网格：验证除了封闭区域被填色，其它地方是否一致
    fill_colors = set()
    for r in range(height):
        for c in range(width):
            if (r, c) in enclosed_pixels:
                fill_colors.add(output_grid[r][c])
            else:
                if input_grid[r][c] != output_grid[r][c]:
                    return None # 外部环境变了，不属于单纯的 Flood Fill

    # 如果封闭区域颜色改变了，且只用了一种或少数几种颜色填充，则触发规则
    if len(fill_colors) > 0 and 0 not in fill_colors:
        return {"filled_colors": list(fill_colors), "filled_area_size": len(enclosed_pixels)}
    
    return None

def detect_gravity(input_grid, output_grid):
    """
    机制 3: 引力机制。检测是否所有的非零像素都保持相对顺序，掉落到了底部或推到了侧边。
    这里实现最常见的 Vertical Gravity (垂直重力掉落)。
    """
    if len(input_grid) != len(output_grid) or len(input_grid[0]) != len(output_grid[0]):
        return None

    height, width = len(input_grid), len(input_grid[0])
    gravity_detected = False

    for c in range(width):
        # 获取输入列和输出列中所有的非0元素（按原有顺序）
        input_col_items = [input_grid[r][c] for r in range(height) if input_grid[r][c] != 0]
        output_col_items = [output_grid[r][c] for r in range(height) if output_grid[r][c] != 0]
        
        # 掉落过程中，同列物体的颜色和数量必须一致
        if input_col_items != output_col_items:
            return None
            
        # 检查 Output 中这些物体是否紧紧贴在底部
        expected_output_col = [0] * (height - len(input_col_items)) + input_col_items
        actual_output_col = [output_grid[r][c] for r in range(height)]
        
        if expected_output_col != actual_output_col:
            return None
            
        if len(input_col_items) > 0 and input_grid != output_grid:
            gravity_detected = True

    if gravity_detected:
        return {"direction": "down"}
    return None

def detect_line_drawing(input_grid, output_grid):
    """
    机制 1: 路径与连通机制。启发式检测：输出网格是否在原有的端点之间“多出了连续的线条”。
    """
    if len(input_grid) != len(output_grid) or len(input_grid[0]) != len(output_grid[0]):
        return None

    height, width = len(input_grid), len(input_grid[0])
    added_pixels = []
    line_colors = set()

    # 找出所有新增的像素
    for r in range(height):
        for c in range(width):
            if input_grid[r][c] != output_grid[r][c] and input_grid[r][c] == 0:
                added_pixels.append((r, c))
                line_colors.add(output_grid[r][c])
            elif input_grid[r][c] != output_grid[r][c] and input_grid[r][c] != 0:
                # 如果把已有的颜色改了，说明不仅是画线，暂不判定为纯画线逻辑
                return None

    if not added_pixels or len(line_colors) > 2:
        return None # 没有新增像素，或者新增颜色太乱（线条通常为1-2种颜色）

    # 简单启发：如果只增加了特定颜色的像素，并且数量达到构成路径的规模，则判定为 drawing
    return {"line_colors": list(line_colors), "path_length": len(added_pixels)}

# ==========================================
# Rule Aggregator
# ==========================================

def detect_all_rules(input_grid, output_grid):
    results = {
        "unchanged": detect_unchanged(input_grid, output_grid),
        "recolor": detect_recolor(input_grid, output_grid),
        "rotation": detect_rotation(input_grid, output_grid),
        "reflection": detect_reflection(input_grid, output_grid),
        "crop": detect_crop(input_grid, output_grid),
        "scale_up": detect_scale_up(input_grid, output_grid),
        "tile_repeat": detect_tile_repeat(input_grid, output_grid),
        "translation": detect_translation(input_grid, output_grid),
        
        # 新增的核心引擎特征提取
        "color_substitution": detect_color_substitution(input_grid, output_grid),
        "flood_fill": detect_flood_fill(input_grid, output_grid),
        "gravity": detect_gravity(input_grid, output_grid),
        "line_drawing": detect_line_drawing(input_grid, output_grid)
    }

    return results
