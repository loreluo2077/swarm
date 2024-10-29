from swarm.repl import run_demo_loop
from agents import triage_agent

from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    run_demo_loop(triage_agent)
