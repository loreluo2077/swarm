from swarm import Swarm, Agent
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

client = Swarm()

english_agent = Agent(
    model="openai/gpt-3.5-turbo",
    name="English Agent",
    instructions="You only speak English.",
)

chinese_agent = Agent(
    model="openai/gpt-3.5-turbo",
    name="Chinese Agent",
    instructions="You only speak Chinese (Mandarin). Always respond in simplified Chinese characters.",
)


def transfer_to_chinese_agent():
    """Transfer Chinese speaking users immediately."""
    return chinese_agent


english_agent.functions.append(transfer_to_chinese_agent)

messages = [{"role": "user", "content": "你好吗?"}]
response = client.run(agent=english_agent, messages=messages,debug=True)

print(response.messages[-1]["content"])
