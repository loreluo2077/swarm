from swarm.repl import run_demo_loop
from agents import dm_agent
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    run_demo_loop(dm_agent, stream=True,debug=True)
