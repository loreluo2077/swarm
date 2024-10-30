import json
from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
import random
from prompt import system_prompt
from swarm import Agent


# Agent definition
dm_agent = Agent(
    name="游戏主持人",
    instructions=system_prompt ,
)
