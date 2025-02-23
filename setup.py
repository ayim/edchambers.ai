from setuptools import setup, find_packages

setup(
    name="edchambers_ai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "langchain-groq",
        "langgraph",
        "langmem",
        "pydantic",
        "python-dotenv",
        "obs-websocket-py"
    ]
)
