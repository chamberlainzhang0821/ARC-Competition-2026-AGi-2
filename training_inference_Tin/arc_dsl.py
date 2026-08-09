import numpy as np
import collections

def recolor(grid, color_map):
    """将矩阵中的颜色按字典映射替换，例如 {5: 1, 0: 2}"""
    arr = np.array(grid)
    for src, dst in color_map.items():
        arr[arr == src] = dst
    return arr.tolist()

def repeat_tile(grid, row_repeats, col_repeats):
    """平铺重复矩阵"""
    return np.tile(np.array(grid), (row_repeats, col_repeats)).tolist()

def scale_up(grid, row_scale, col_scale):
    """按倍率放大矩阵元素"""
    return np.repeat(np.repeat(np.array(grid), row_scale, axis=0), col_scale, axis=1).tolist()

def kronecker_expand(grid, pattern):
    """克罗内克积分形扩张：用 pattern 替换 grid 中的非零单元格"""
    g_arr = np.array(grid)
    p_arr = np.array(pattern)
    out_h = g_arr.shape[0] * p_arr.shape[0]
    out_w = g_arr.shape[1] * p_arr.shape[1]
    res = np.zeros((out_h, out_w), dtype=int)
    
    for r in range(g_arr.shape[0]):
        for c in range(g_arr.shape[1]):
            if g_arr[r, c] != 0:
                r_start, r_end = r * p_arr.shape[0], (r + 1) * p_arr.shape[0]
                c_start, c_end = c * p_arr.shape[1], (c + 1) * p_arr.shape[1]
                res[r_start:r_end, c_start:c_end] = p_arr
    return res.tolist()

def apply_gravity(grid, direction="down"):
    """垂直重力模拟：让非零像素下落"""
    arr = np.array(grid)
    height, width = arr.shape
    new_grid = np.zeros_like(arr)
    for c in range(width):
        col_vals = [v for v in arr[:, c] if v != 0]
        if direction == "down":
            new_grid[height - len(col_vals):, c] = col_vals
    return new_grid.tolist()
