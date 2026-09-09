import os

from dotenv import load_dotenv


def setup_tracing(project_name="meme-agent"):
    load_dotenv()

    if os.getenv("LANGCHAIN_API_KEY"):
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = project_name
