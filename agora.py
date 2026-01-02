from langchain.chat_models import init_chat_model
from rich import print
model = init_chat_model(
    "gemini-flash-lite-latest",
    model_provider="google_genai",
    temperature=0,  
    
)
print(model)