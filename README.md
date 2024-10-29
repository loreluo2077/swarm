![Swarm Logo](assets/logo.png)

# Swarm (实验性质，教育用途)

一个探索人性化、轻量级多智能体编排的教育框架。

> [!警告]
> Swarm 目前是一个实验性的示例框架，旨在探索多智能体系统的人性化接口。它不适合在生产环境中使用，因此没有官方支持。（这也意味着我们不会审查 PR 或 issues！）
>
> Swarm 的主要目标是展示在 [编排智能体：交接与例程](https://cookbook.openai.com/examples/orchestrating_agents) 手册中探索的交接和例程模式。它不是一个独立的库，主要用于教育目的。

## 安装

需要 Python 3.10+

```shell
pip install git+ssh://git@github.com/openai/swarm.git
```

或者

```shell
pip install git+https://github.com/openai/swarm.git
```

## 使用方法

```python
from swarm import Swarm, Agent

client = Swarm()

def transfer_to_agent_b():
    return agent_b


agent_a = Agent(
    name="Agent A",
    instructions="你是一个有帮助的智能体。",
    functions=[transfer_to_agent_b],
)

agent_b = Agent(
    name="Agent B",
    instructions="只用俳句说话。",
)

response = client.run(
    agent=agent_a,
    messages=[{"role": "user", "content": "我想和智能体 B 对话。"}],
)

print(response.messages[-1]["content"])
```

```
希望闪耀亮，
新路优雅汇聚，
我能帮什么？
```

## 目录

- [概述](#概述)
- [示例](#示例)
- [文档](#文档)
  - [运行 Swarm](#运行-swarm)
  - [智能体](#智能体)
  - [函数](#函数)
  - [流式处理](#流式处理)
- [评估](#评估)
- [工具](#工具)

# 概述

Swarm 专注于使智能体的**协调**和**执行**变得轻量级、高度可控且易于测试。

它通过两个基本抽象来实现这一点：`Agent`（智能体）和**交接**。一个`智能体`包含`instructions`（指令）和`tools`（工具），并且可以在任何时候选择将对话交给另一个`智能体`。

这些基本要素足以表达工具和智能体网络之间的丰富动态，让你能够构建可扩展的、实际的解决方案，同时避免陡峭的学习曲线。

> [!注意]
> Swarm 智能体与 Assistants API 中的助手无关。它们的命名相似只是为了方便，但在其他方面完全无关。Swarm 完全由 Chat Completions API 驱动，因此在调用之间是无状态的。

## 为什么选择 Swarm

Swarm 探索了本质上轻量级、可扩展且高度可定制的模式。类似 Swarm 的方法最适合处理大量独立功能和难以编码到单个提示中的指令的情况。

The Assistants API is a great option for developers looking for fully-hosted threads and built in memory management and retrieval. However, Swarm is an educational resource for developers curious to learn about multi-agent orchestration. Swarm runs (almost) entirely on the client and, much like the Chat Completions API, does not store state between calls.

# Examples

查看 `/examples` 目录获取灵感！在每个示例的 README 中了解更多详情。

- [`basic`](examples/basic)：基础示例，包括设置、函数调用、交接和上下文变量等基础知识
- [`triage_agent`](examples/triage_agent)：设置基础分流步骤以转交给正确智能体的简单示例
- [`weather_agent`](examples/weather_agent)：函数调用的简单示例
- [`airline`](examples/airline)：在航空公司场景下处理不同客户服务请求的多智能体设置
- [`support_bot`](examples/support_bot)：包含用户界面智能体和具有多个工具的帮助中心智能体的客户服务机器人
- [`personal_shopper`](examples/personal_shopper)：可以帮助进行销售和订单退款的个人购物智能体


# Documentation

![Swarm Diagram](assets/swarm_diagram.png)

## Running Swarm

Start by instantiating a Swarm client (which internally just instantiates an `OpenAI` client).

```python
from swarm import Swarm

client = Swarm()
```

### `client.run()`

Swarm 的 `run()` 函数类似于 Chat Completions API 中的 `chat.completions.create()` 函数 —— 它接收 `messages` 并返回 `messages`，且在调用之间不保存状态。重要的是，它还处理智能体函数执行、交接、上下文变量引用，并且在返回给用户之前可以进行多轮对话。

从本质上讲，Swarm 的 `client.run()` 实现了以下循环：

1. 从当前智能体获取完成结果
2. 执行工具调用并附加结果
3. 必要时切换智能体
4. 必要时更新上下文变量
5. 如果没有新的函数调用，则返回


#### 参数

| 参数                  | 类型     | 描述                                                                                                                                | 默认值          |
| --------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| **agent**             | `Agent` | 要调用的（初始）智能体                                                                                                              | (必需)         |
| **messages**          | `List`  | 消息对象列表，与 [Chat Completions `messages`](https://platform.openai.com/docs/api-reference/chat/create#chat-create-messages) 相同 | (必需)         |
| **context_variables** | `dict`  | 附加上下文变量的字典，可用于函数和智能体指令                                                                                        | `{}`           |
| **max_turns**         | `int`   | 允许的最大对话轮次                                                                                                                  | `float("inf")` |
| **model_override**    | `str`   | 可选字符串，用于覆盖智能体使用的模型                                                                                                | `None`         |
| **execute_tools**     | `bool`  | 如果为 `False`，当智能体尝试调用函数时中断执行并立即返回 `tool_calls` 消息                                                          | `True`         |
| **stream**            | `bool`  | 如果为 `True`，启用流式响应                                                                                                         | `False`        |
| **debug**             | `bool`  | 如果为 `True`，启用调试日志                                                                                                         | `False`        |

当 `client.run()` 完成后（可能经过多次调用智能体和工具），它将返回一个包含所有相关更新状态的 `Response`。具体包括新的 `messages`、最后调用的 `Agent` 和最新的 `context_variables`。你可以将这些值（加上新的用户消息）传入下一次执行 `client.run()` 以继续交互 —— 类似于 `chat.completions.create()`。（`run_demo_loop` 函数在 `/swarm/repl/repl.py` 中实现了一个完整执行循环的示例。）

#### `Response` 字段

| 字段                  | 类型     | 描述                                                                                                                                                                                                                    |
| --------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **messages**          | `List`  | 对话过程中生成的消息对象列表。与 [Chat Completions `messages`](https://platform.openai.com/docs/api-reference/chat/create#chat-create-messages) 非常相似，但增加了 `sender` 字段来指示消息来自哪个 `Agent`。           |
| **agent**             | `Agent` | 最后处理消息的智能体。                                                                                                                                                                                                   |
| **context_variables** | `dict`  | 与输入变量相同，外加任何变更。                                                                                                                                                                                           |

## 智能体

一个 `Agent` 简单地封装了一组 `instructions`（指令）和一组 `functions`（函数）（以及下面的一些额外设置），并且具有将执行权交给另一个 `Agent` 的能力。

虽然很容易将 `Agent` 拟人化为"做 X 的某人"，但它也可以用来表示由一组 `instructions` 和 `functions` 定义的非常具体的工作流程或步骤（例如，一组步骤、复杂的检索、单个数据转换步骤等）。这允许将 `Agent` 组合成"智能体"、"工作流程"和"任务"的网络，所有这些都由相同的基本元素表示。

## `Agent` 字段

| 字段             | 类型                      | 描述                                           | 默认值                        |
| ---------------- | ------------------------- | --------------------------------------------- | ---------------------------- |
| **name**         | `str`                     | 智能体的名称                                   | `"Agent"`                    |
| **model**        | `str`                     | 智能体使用的模型                               | `"gpt-4"`                    |
| **instructions** | `str` 或 `func() -> str`  | 智能体的指令，可以是字符串或返回字符串的可调用对象 | `"You are a helpful agent."` |
| **functions**    | `List`                    | 智能体可以调用的函数列表                        | `[]`                         |
| **tool_choice**  | `str`                     | 智能体的工具选择（如果有）                      | `None`                       |



### Instructions

`Agent` 的 `instructions` 直接转换为对话中的 `system` 提示（作为第一条消息）。在任何给定时刻，只有活动 `Agent` 的 `instructions` 会出现（例如，如果发生 `Agent` 交接，`system` 提示会改变，但聊天历史记录不会改变。）

```python
agent = Agent(
   instructions="你是一个有帮助的智能体。"
)
```

`instructions` 可以是普通的 `str`，也可以是返回 `str` 的函数。该函数可以选择接收 `context_variables` 参数，该参数将由传入 `client.run()` 的 `context_variables` 填充。

```python
def instructions(context_variables):
   user_name = context_variables["user_name"]
   return f"帮助用户 {user_name} 完成他们想做的任何事。"

agent = Agent(
   instructions=instructions
)
response = client.run(
   agent=agent,
   messages=[{"role":"user", "content": "你好！"}],
   context_variables={"user_name":"小明"}
)
print(response.messages[-1]["content"])
```

```
你好小明，我今天能为你做些什么？
```

## Functions

- Swarm `Agent` 可以直接调用 Python 函数。
- 函数通常应该返回 `str`（返回值会尝试被转换为 `str`）。
- 如果函数返回一个 `Agent`，执行将转移到该 `Agent`。
- 如果函数定义了 `context_variables` 参数，它将由传入 `client.run()` 的 `context_variables` 填充。

```python
def greet(context_variables, language):
   user_name = context_variables["user_name"]
   greeting = "你好" if language.lower() == "chinese" else "Hello"
   print(f"{greeting}, {user_name}!")
   return "完成"

agent = Agent(
   functions=[greet]
)

client.run(
   agent=agent,
   messages=[{"role": "user", "content": "请使用 greet() 函数。"}],
   context_variables={"user_name": "小明"}
)
```

```
你好，小明！
```

- 如果 `Agent` 函数调用出现错误（缺少函数、参数错误、执行错误），错误响应将被添加到聊天中，以便 `Agent` 可以优雅地恢复。
- 如果 `Agent` 调用多个函数，它们将按顺序执行。

### Handoffs and Updating Context Variables

An `Agent` 可以通过在 `function` 中返回另一个 `Agent` 来进行交接。

```python
sales_agent = Agent(name="销售智能体")

def transfer_to_sales():
   return sales_agent

agent = Agent(functions=[transfer_to_sales])

response = client.run(agent, [{"role":"user", "content":"转接我到销售部门。"}])
print(response.agent.name)
```

```
销售智能体
```

它还可以通过返回更完整的 `Result` 对象来更新 `context_variables`。这也可以包含 `value` 和 `agent`，以防你想要一个函数同时返回值、更新智能体和更新上下文变量（或这三者的任意组合）。

```python
sales_agent = Agent(name="销售智能体")

def talk_to_sales():
   print("你好，世界！")
   return Result(
       value="完成",
       agent=sales_agent,
       context_variables={"department": "sales"}
   )

agent = Agent(functions=[talk_to_sales])

response = client.run(
   agent=agent,
   messages=[{"role": "user", "content": "转接我到销售部门"}],
   context_variables={"user_name": "小明"}
)
print(response.agent.name)
print(response.context_variables)
```

```
销售智能体
{'department': 'sales', 'user_name': '小明'}
```

> [!注意]
> 如果 `Agent` 调用多个函数来交接到其他 `Agent`，只有最后一个交接函数会被使用。

### Function Schemas

Swarm 自动将函数转换为传入 Chat Completions `tools` 的 JSON Schema。

- 文档字符串转换为函数 `description`。
- 没有默认值的参数设置为 `required`。
- 类型提示映射到参数的 `type`（默认为 `string`）。
- 不明确支持每个参数的描述，但如果直接添加到文档字符串中应该也能类似工作。（将来可能会添加文档字符串参数解析。）

```python
def greet(name, age: int, location: str = "北京"):
   """向用户问好。确保在调用前获取他们的姓名和年龄。

   参数:
      name: 用户姓名。
      age: 用户年龄。
      location: 最棒的地方。
   """
   print(f"你好 {name}，很高兴知道你在 {location} 已经 {age} 岁了！")
```

```javascript
{
   "type": "function",
   "function": {
      "name": "greet",
      "description": "向用户问好。确保在调用前获取他们的姓名和年龄。\n\n参数:\n   name: 用户姓名。\n   age: 用户年龄。\n   location: 最棒的地方。",
      "parameters": {
         "type": "object",
         "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "location": {"type": "string"}
         },
         "required": ["name", "age"]
      }
   }
}
```

## Streaming

```python
stream = client.run(agent, messages, stream=True)
for chunk in stream:
   print(chunk)
```

使用与 [Chat Completions API 流式处理](https://platform.openai.com/docs/api-reference/streaming) 相同的事件。请参见 `/swarm/repl/repl.py` 中的 `process_and_print_streaming_response` 作为示例。

添加了两种新的事件类型：

- `{"delim":"start"}` 和 `{"delim":"end"}`，用于标识每次 `Agent` 处理单个消息（响应或函数调用）的时机。这有助于识别 `Agent` 之间的切换。
- `{"response": Response}` 将在流的末尾返回带有聚合（完整）响应的 `Response` 对象，以方便使用。

# Evaluations

评估对任何项目都至关重要，我们鼓励开发者带来自己的评估套件来测试其 swarm 的性能。作为参考，我们在 `airline`、`weather_agent` 和 `triage_agent` 快速入门示例中提供了一些评估 swarm 的示例。更多详情请参见各自的 README。

# Utils

使用 `run_demo_loop` 来测试你的 swarm！这将在命令行上运行一个 REPL。支持流式处理。

```python
from swarm.repl import run_demo_loop
...
run_demo_loop(agent, stream=True)
```

# Core Contributors

- Ilan Bigio - [ibigio](https://github.com/ibigio)
- James Hills - [jhills20](https://github.com/jhills20)
- Shyamal Anadkat - [shyamal-anadkat](https://github.com/shyamal-anadkat)
- Charu Jaiswal - [charuj](https://github.com/charuj)
- Colin Jarvis - [colin-openai](https://github.com/colin-openai)
- Katia Gil Guzman - [katia-openai](https://github.com/katia-openai)
