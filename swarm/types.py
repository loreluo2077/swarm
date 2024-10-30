# 从openai库导入聊天相关的类型定义
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from typing import List, Callable, Union, Optional

# 导入pydantic库用于数据验证和设置
from pydantic import BaseModel

# 从os模块导入getenv函数用于获取环境变量
from os import getenv

# 定义一个类型别名：AgentFunction是一个可调用对象(函数)，
# 返回类型可以是字符串、Agent对象或字典
AgentFunction = Callable[[], Union[str, "Agent", dict]]



# 获取默认模型,如果环境变量未设置则使用gpt-4作为默认值
DEFAULT_MODEL = getenv("DEFAULT_MODEL", "gpt-4")


class Agent(BaseModel):
    """AI代理的基本配置类"""
    name: str = "Agent"                # 代理名称
    model: str = DEFAULT_MODEL             # 使用的AI模型
    instructions: Union[str, Callable[[], str]] = "You are a helpful agent."  # 代理的指令/提示词
    functions: List[AgentFunction] = [] # 代理可以使用的函数列表
    tool_choice: str = None            # 工具选择
    parallel_tool_calls: bool = True    # 是否允许并行调用工具


class Response(BaseModel):
    """响应类，用于存储代理的响应信息"""
    messages: List = []                # 消息历史
    agent: Optional[Agent] = None      # 相关的代理实例
    context_variables: dict = {}       # 上下文变量


class Result(BaseModel):
    """
    封装代理函数的返回值
    
    属性:
        value (str): 结果值（字符串形式）
        agent (Agent): 代理实例（如果适用）
        context_variables (dict): 上下文变量字典
    """
    value: str = ""                    # 返回的结果值
    agent: Optional[Agent] = None      # 相关的代理实例
    context_variables: dict = {}       # 上下文变量
