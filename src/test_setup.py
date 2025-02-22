from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os

def test_langchain_setup():
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Create a simple prompt template
        template = "Tell me a short joke about {topic}"
        prompt = PromptTemplate(template=template, input_variables=["topic"])
        
        # Create a model (this will require an API key to actually run)
        llm = ChatOpenAI(
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create a chain
        chain = LLMChain(llm=llm, prompt=prompt)
        
        print("LangChain setup test successful!")
        print("Note: To run the chain, please set your OPENAI_API_KEY in the .env file")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
if __name__ == "__main__":
    test_langchain_setup() 