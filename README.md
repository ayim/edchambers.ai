# LangChain Project

This is a Python project set up with LangChain dependencies for building applications with Large Language Models (LLMs).

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add your API keys:
```env
OPENAI_API_KEY=your_api_key_here
```

## Project Structure

```
.
├── README.md
├── requirements.txt
├── src/
│   └── __init__.py
└── .env
```

## Dependencies

- `langchain`: Main LangChain library for building LLM applications
- `langchain-core`: Core LangChain functionality
- `langchain-community`: Community integrations for LangChain
- `python-dotenv`: Environment variable management
- `openai`: OpenAI API client
- `chromadb`: Vector store for embeddings
- `tiktoken`: OpenAI's tokenizer
- `beautifulsoup4`: HTML parsing
- `requests`: HTTP client
- `pydantic`: Data validation

## Getting Started

1. Activate your virtual environment
2. Set up your environment variables in `.env`
3. Start building your LangChain application in the `src` directory

## Best Practices

- Keep your API keys secure and never commit them to version control
- Use environment variables for configuration
- Follow the LangChain documentation for best practices and patterns
- Consider using async operations for better performance 