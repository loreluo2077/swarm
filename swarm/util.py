import inspect
from datetime import datetime


def debug_print(debug: bool, *args: str) -> None:
    """
    调试打印函数
    Args:
        debug: 是否启用调试输出
        args: 要打印的消息参数
    """
    if not debug:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = " ".join(map(str, args))
    print(f"\033[97m[\033[90m{timestamp}\033[97m]\033[90m {message}\033[0m")


def merge_fields(target, source):
    """
    递归合并两个字典的字段
    Args:
        target: 目标字典
        source: 源字典
    """
    for key, value in source.items():
        if isinstance(value, str):
            # 对于 type 字段，直接赋值而不是拼接
            if key == "type":
                target[key] = value
            else:
                target[key] += value
        elif value is not None and isinstance(value, dict):
            merge_fields(target[key], value)


def merge_chunk(final_response: dict, delta: dict) -> None:
    """
    合并响应块
    专门用于合并API响应块的函数
    Args:
        final_response: 最终响应字典
        delta: 需要合并的增量响应


    """
    # 1. 如果是第一个块（包含role字段），设置sender
    if "role" in delta:
        final_response["role"] = delta["role"]
        if "sender" in delta:
            final_response["sender"] = delta["sender"]
        delta.pop("role", None)
        delta.pop("sender", None)

    # 2. 合并基本字段（如 content）
    merge_fields(final_response, delta)
    try:
        # 3. 特殊处理 tool_calls 字段
        tool_calls = delta.get("tool_calls")
        if tool_calls and len(tool_calls) > 0:
            # 获取并移除索引
            index = tool_calls[0].pop("index")
            # 合并到对应索引的 tool_call
            merge_fields(final_response["tool_calls"][index], tool_calls[0])
    except (KeyError, IndexError) as e:
        print(f"Error merging tool_calls: {e}")

def function_to_json(func) -> dict:
    """
    将Python函数转换为JSON格式的字典描述
    Args:
        func: 要转换的函数
    Returns:
        包含函数签名信息的字典
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        # 获取函数的签名信息
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
     # 遍历所有参数
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"type": param_type}

    # 获取所有必需参数
    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }
