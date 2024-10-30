# Standard library imports
import copy
import json
from collections import defaultdict
from typing import List, Callable, Union

# Package/library imports
from openai import OpenAI


# Local imports
from .util import function_to_json, debug_print, merge_chunk
from .types import (
    Agent,
    AgentFunction,
    ChatCompletionMessage,
    ChatCompletionMessageToolCall,
    Function,
    Response,
    Result,
)

__CTX_VARS_NAME__ = "context_variables"


class Swarm:
    def __init__(self, client=None):
        if not client:
            client = OpenAI()
        self.client = client

    def get_chat_completion(
        self,
        agent: Agent,          # Agent对象，包含模型配置和函数定义
        history: List,         # 对话历史记录
        context_variables: dict,  # 上下文变量
        model_override: str,   # 可选的模型覆盖设置
        stream: bool,          # 是否使用流式响应
        debug: bool,          # 是否启用调试输出
    ) -> ChatCompletionMessage:  # 返回类型是ChatCompletionMessage

        # 使用defaultdict处理上下文变量，如果键不存在返回空字符串
        context_variables = defaultdict(str, context_variables)
        
        # 获取agent的指令
        instructions = (
            agent.instructions(context_variables)  # 如果 agent.instructions 是函数就执行这部分
            if callable(agent.instructions)
            else agent.instructions # 如果不是函数就执行这部分
        )
        
        # 构建消息列表：系统指令 + 历史消息
        messages = [{"role": "system", "content": instructions}] + history
        
        # 调试输出
        debug_print(debug, "Getting chat completion for...:", messages)

        # 将agent的函数转换为OpenAI API需要的JSON格式
        tools = [function_to_json(f) for f in agent.functions]
        
        # 处理工具中的上下文变量
        for tool in tools:
            params = tool["function"]["parameters"]
            # 从工具参数中移除上下文变量
            params["properties"].pop(__CTX_VARS_NAME__, None)
            # 从必需参数中移除上下文变量
            if __CTX_VARS_NAME__ in params["required"]:
                params["required"].remove(__CTX_VARS_NAME__)

        # 准备API调用参数
        create_params = {
            "model": model_override or agent.model,  # 使用覆盖模型或agent默认模型
            "messages": messages,                    # 消息历史
            "tools": tools or None,                 # 可用的工具/函数
            "tool_choice": agent.tool_choice,       # 工具选择设置
            "stream": stream,                       # 是否流式输出
        }

        debug_print(debug, "Creating chat completion with params:", create_params)

        # 如果有工具，添加并行工具调用设置
        if tools:
            create_params["parallel_tool_calls"] = agent.parallel_tool_calls

        # 调用OpenAI API并返回结果
        return self.client.chat.completions.create(**create_params)

    def handle_function_result(self, result, debug) -> Result:
        """
        处理函数调用的返回结果，将其转换为标准的Result对象  
        Args:
            result: 函数返回的原始结果
            debug: 是否启用调试输出
        Returns:
            Result: 标准化后的结果对象
        """
        match result:
            case Result() as result:
                # 如果已经是Result对象则直接返回
                return result

            case Agent() as agent:
                # 如果返回的是Agent对象,包装成Result并返回
                return Result(
                    value=json.dumps({"assistant": agent.name}),
                    agent=agent,
                )
            case _:
                # 处理其他类型的返回值
                try:
                    # 尝试转换为字符串并包装成Result
                    return Result(value=str(result))
                except Exception as e:
                    # 转换失败时抛出类型错误
                    error_message = f"Failed to cast response to string: {result}. Make sure agent functions return a string or Result object. Error: {str(e)}"
                    debug_print(debug, error_message)
                    raise TypeError(error_message)

    def handle_tool_calls(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],  # AI请求调用的工具列表
        functions: List[AgentFunction], # 可用的函数列表
        context_variables: dict, # 上下文变量
        debug: bool, # 是否开启调试
    ) -> Response:
         # 创建函数名到函数的映射字典
        function_map = {f.__name__: f for f in functions}
        # 初始化响应对象
        partial_response = Response(
            messages=[], agent=None, context_variables={})

        # 遍历每个工具调用
        for tool_call in tool_calls:
            name = tool_call.function.name
            # handle missing tool case, skip to next tool
            if name not in function_map:
                debug_print(debug, f"Tool {name} not found in function map.")
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "tool_name": name,
                        "content": f"Error: Tool {name} not found.",
                    }
                )
                continue
             # 2. 解析函数参数
            args = json.loads(tool_call.function.arguments)
            debug_print(
                debug, f"Processing tool call: {name} with arguments {args}")

            # 3. 获取要调用的函数
            func = function_map[name]
            # 4. 如果函数需要上下文变量，则传入
            if __CTX_VARS_NAME__ in func.__code__.co_varnames:
                args[__CTX_VARS_NAME__] = context_variables

            # 5. 执行函数
            raw_result = function_map[name](**args)

            # 6. 处理函数返回结果
            result: Result = self.handle_function_result(raw_result, debug)
             # 7. 添加执行结果到响应消息
            partial_response.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "tool_name": name,
                    "content": result.value,
                }
            )
            # 8. 更新上下文变量和代理
            partial_response.context_variables.update(result.context_variables)
            if result.agent:
                partial_response.agent = result.agent

        return partial_response

    def run_and_stream(
        self,
        agent: Agent,
        messages: List,
        context_variables: dict = {},
        model_override: str = None,
        debug: bool = False,
        max_turns: int = float("inf"),
        execute_tools: bool = True,
    ):
        active_agent = agent
        context_variables = copy.deepcopy(context_variables)
        history = copy.deepcopy(messages)
        init_len = len(messages)

        while len(history) - init_len < max_turns:

            message = {
                "content": "",
                "sender": agent.name,
                "role": "assistant",
                "function_call": None,
                "tool_calls": defaultdict(
                    lambda: {
                        "function": {"arguments": "", "name": ""},
                        "id": "",
                        "type": "",
                    }
                ),
            }

            # get completion with current history, agent
            completion = self.get_chat_completion(
                agent=active_agent,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                stream=True,
                debug=debug,
            )

            yield {"delim": "start"}
            for chunk in completion:
                delta = json.loads(chunk.choices[0].delta.json())
                if delta["role"] == "assistant":
                    delta["sender"] = active_agent.name
                yield delta
                delta.pop("role", None)
                delta.pop("sender", None)
                merge_chunk(message, delta)
            yield {"delim": "end"}

            message["tool_calls"] = list(
                message.get("tool_calls", {}).values())
            if not message["tool_calls"]:
                message["tool_calls"] = None
            debug_print(debug, "Received completion:", message)
            history.append(message)

            if not message["tool_calls"] or not execute_tools:
                debug_print(debug, "Ending turn.")
                break

            # convert tool_calls to objects
            tool_calls = []
            for tool_call in message["tool_calls"]:
                function = Function(
                    arguments=tool_call["function"]["arguments"],
                    name=tool_call["function"]["name"],
                )
                tool_call_object = ChatCompletionMessageToolCall(
                    id=tool_call["id"], function=function, type=tool_call["type"]
                )
                tool_calls.append(tool_call_object)

            # handle function calls, updating context_variables, and switching agents
            partial_response = self.handle_tool_calls(
                tool_calls, active_agent.functions, context_variables, debug
            )
            history.extend(partial_response.messages)
            context_variables.update(partial_response.context_variables)
            if partial_response.agent:
                active_agent = partial_response.agent

        yield {
            "response": Response(
                messages=history[init_len:],
                agent=active_agent,
                context_variables=context_variables,
            )
        }

    def run(
        self,
        agent: Agent,                    # AI助手的配置
        messages: List,                  # 对话历史
        context_variables: dict = {},    # 上下文变量（默认空字典）
        model_override: str = None,      # 可以临时更换模型
        stream: bool = False,            # 是否流式输出
        debug: bool = False,             # 是否显示调试信息
        max_turns: int = float("inf"),   # 最大对话轮数
        execute_tools: bool = True,      # 是否执行工具
    ) -> Response:
        if stream:
            return self.run_and_stream(
                agent=agent,
                messages=messages,
                context_variables=context_variables,
                model_override=model_override,
                debug=debug,
                max_turns=max_turns,
                execute_tools=execute_tools,
            )
        active_agent = agent
        context_variables = copy.deepcopy(context_variables)
        history = copy.deepcopy(messages)
        init_len = len(messages)

        # 1. 初始化
        active_agent = agent                              # 当前活动的AI助手
        context_variables = copy.deepcopy(context_variables)  # 复制上下文变量
        history = copy.deepcopy(messages)                 # 复制对话历史
        init_len = len(messages)                          # 记录初始消息数量

        # 2. 主要对话循环
        while len(history) - init_len < max_turns and active_agent:
            # 2.1 获取AI的回复
            completion = self.get_chat_completion(
                agent=active_agent,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                stream=stream,
                debug=debug,
            )
            
            # 2.2 处理AI的回复
            message = completion.choices[0].message
            debug_print(debug, "Received completion:", message)
            
            # 2.3 添加发送者信息并保存到历史记录
            message.sender = active_agent.name
            history.append(json.loads(message.model_dump_json()))

            # 2.4 如果没有工具调用或不执行工具，结束对话
            if not message.tool_calls or not execute_tools:
                debug_print(debug, "Ending turn.")
                break

            # 2.5 处理工具调用
            partial_response = self.handle_tool_calls(
                message.tool_calls, 
                active_agent.functions, 
                context_variables, 
                debug
            )
            
            # 2.6 更新历史和变量
            history.extend(partial_response.messages)
            context_variables.update(partial_response.context_variables)
            
            # 2.7 如果需要切换AI助手
            if partial_response.agent:
                active_agent = partial_response.agent

        # 3. 返回最终结果
        return Response(
            messages=history[init_len:],     # 只返回新的消息
            agent=active_agent,              # 当前的AI助手
            context_variables=context_variables  # 更新后的上下文变量
        )
