'''every linear transformation is a matrix transformation. 
the difference between the general linear transformation is that the matrices here might become bigger, or smaller'''

RULE_LIBRARY = {
    "identity": [
        "unchanged"
    ],

    "movement": [
        "translate",
        "move_to_edge",
        "move_to_corner"
    ],

    "color_change": [
        "recolor_object",
        "replace_one_color"
    ],

    "copy": [
        "duplicate",
        "repeat_horizontal",
        "repeat_vertical"
    ],

    "shape_change": [
        "rotate",
        "reflect",
        "resize"
    ],

    "grid_change": [
        "crop",
        "expand",
        "fill_region"
    ],

    "object_change": [
        "delete_object",
        "connect_objects",
        "split_object"
    ],

    "pattern": [
        "extend_pattern",
        "complete_pattern"
    ]
}


