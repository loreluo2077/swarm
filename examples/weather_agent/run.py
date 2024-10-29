from swarm.repl import run_demo_loop
from agents import weather_agent
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    run_demo_loop(weather_agent, stream=True)
