# 初始响应结构
final_response = {
    "role": "assistant",
    "content": "",
    "tool_calls": [
        {
            "function": {
                "name": "",
                "arguments": ""
            }
        }
    ]
}

# 第一个数据块
chunk1 = {
    "role": "assistant", 
    "content": "让我帮你查询",
    "tool_calls": [{
        "index": 0,
        "function": {
            "name": "get_",
            "arguments": '{"city":'
        }
    }]
}

# 第二个数据块 
chunk2 = {
    "content": "天气",
    "tool_calls": [{
        "index": 0,
        "function": {
            "name": "weather",
            "arguments": '"shanghai"}'
        }
    }]
}

# 处理过程
merge_chunk(final_response, chunk1)
merge_chunk(final_response, chunk2)

# 最终结果
{
     "role": "assistant",
     "content": "让我帮你查询天气",
     "tool_calls": [{
         "function": {
             "name": "get_weather", 
            "arguments": '{"city":"shanghai"}'
         }
     }]
}

# 关键点解释

1. 为什么要移除 role？
   - role 字段（如 "assistant"）只需要出现一次
   - 通常在第一个响应块中包含，后续块不需要

2. tool_calls 的特殊处理
   - tool_calls 是一个数组
   - 每个 tool_call 都有一个 index 标识它在数组中的位置
   - 需要根据 index 找到正确的位置进行合并

3. 合并过程
   # 基本字段（如 content）的合并
   "让我帮你查询" + "天气" = "让我帮你查询天气"

   # function name 的合并
   "get_" + "weather" = "get_weather"

   # arguments 的合并
   '{"city":' + '"shanghai"}' = '{"city":"shanghai"}'