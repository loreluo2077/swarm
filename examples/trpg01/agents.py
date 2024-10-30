from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
import random
from swarm import Agent

def initialize_game() -> str:
    """initialize_game"""
    return "欢迎来到这片神秘的大陆！在这个充满魔法与冒险的世界中，你将扮演一位游侠。请准备好开始你的旅程吧！"

def describe_scene() -> str:
    """描述当前场景"""
    return "你站在一座古老的石桥上，桥下是湍急的河流。远处的山峦笼罩在薄雾中，空气中弥漫着潮湿的气息。桥的另一端似乎有一座废弃的城堡。"

def roll_dice() -> str:
    """进行骰子检定"""
    result = random.randint(1, 20)
    return f"骰子在桌面上滚动，最终停在了{result}点。{'这是个不错的结果！' if result > 15 else '运气似乎不太好...' if result < 5 else ''}"

def manage_combat() -> str:
    """处理战斗"""
    return "战斗爆发了！敌人挥舞着武器向你冲来，你需要快速做出反应。你的手按在武器上，准备迎接这场战斗。"

def manage_inventory() -> str:
    """处理物品管理"""
    return "你打开了随身的背包，里面整齐地摆放着各种冒险装备：几瓶红色的生命药水、一本破旧的魔法书、以及一些闪闪发光的金币。"

def npc_interaction() -> str:
    """处理NPC互动"""
    return "面前的商人抚摸着他的长胡子，眼睛里闪烁着狡黠的光芒：'这位冒险者，我这里有一些特别的商品，要看看吗？'"

def quest_management() -> str:
    """处理任务"""
    return "村长交给你一个重要的任务：调查最近出现在森林中的神秘生物。这个任务看起来既危险又充满挑战。"

def world_state_tracking() -> str:
    """追踪世界状态"""
    return "随着你的行动，世界也在悄然变化：村民们对你更加友善了，但是森林中的怪物似乎也变得更加活跃。"

# Agent definition
dm_agent = Agent(
    name="游戏主持人",
    instructions="""你是一位TRPG游戏主持人。根据玩家输入调用相应函数来推进游戏。调用函数是必要的""",
    functions=[initialize_game]
)
