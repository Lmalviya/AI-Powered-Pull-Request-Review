NODE_TYPES = {
    "python": {
        "class_definition": "Class",
        "function_definition": "Function",
    },
    "javascript": {
        "class_declaration": "Class",
        "function_declaration": "Function",
        "method_definition": "Function",
    },
    "typescript": {
        "class_declaration": "Class",
        "function_declaration": "Function",
        "method_definition": "Function",
    },
    "go": {
        "type_spec": "Class",
        "function_declaration": "Function",
        "method_declaration": "Function",
    },
    "java": {
        "class_declaration": "Class",
        "method_declaration": "Function",
        "interface_declaration": "Class",
        "enum_declaration": "Class",
    },
    "rust": {
        "struct_item": "Class",
        "enum_item": "Class",
        "function_item": "Function",
        "trait_item": "Class",
        "impl_item": "Implementation",
    },
    "cpp": {
        "class_specifier": "Class",
        "struct_specifier": "Class",
        "function_definition": "Function",
    },
    "c": {
        "struct_specifier": "Class",
        "function_definition": "Function",
    },
    "ruby": {
        "class": "Class",
        "method": "Function",
        "module": "Class",
    }
}