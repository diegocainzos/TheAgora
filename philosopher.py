import operator
from typing import Annotated, List, TypedDict, Dict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

#  DATA MODELS 

class AgoraState(TypedDict):
    # merging messages is crucial for the graph state
    messages: Annotated[List[AnyMessage], operator.add]
    user_input: str

class PhilosopherResponse(BaseModel):
    """
    Enforcing structure to avoid the LLM rambling.
    We split the reaction and advice to make it punchier.
    """
    philosopher_name: str = Field(description="The name of the philosopher speaking (e.g., 'Plato').")
    reaction: str = Field(description="A sharp or biting critique of what the previous philosopher said.")
    advice: str = Field(description="Direct, harsh, and practical advice for the user.")

#  AGENT LOGIC 

class Philosopher:
    # moving this out of __init__ so we don't recreate it every single time.
    # cleaner memory usage.
    PERSONAS: Dict[str, str] = {
        "camus": "Obsessed with the absurd. Life has no meaning, just drink coffee and carry on.",
        "nietzsche": "Aggressive and vitalist. Will to power. Amor Fati.",
        "hegel": "Pedantic. Absolute Spirit. Loves complicated words.",
        "sartre": "Existentialist. Radical freedom. No excuses allowed.",
        "kant": "Rigid moral duty. Discipline. Zero emotions.",
        "plato": "World of ideas. Everything is a shadow. Elitist mystic.",
        "debug": "Technical support / troubleshooter."
    }

    def __init__(self, name: str, model: BaseChatModel, participants: List[str]):
        self.name = name
        
        # binding the schema here.
        # this basically tells the LLM: "don't give me text, give me this JSON object"
        self.structured_model = model.with_structured_output(PhilosopherResponse)

        # dynamic context specific to this instance
        others = [p.title() for p in participants if p != name]
        others_str = ", ".join(others)
        
        # fallback to a generic description if name isn't found
        flavor = self.PERSONAS.get(self.name, "A generic academic philosopher.")

        # constructing the prompt once to save processing time later
        # changed the tone to English but kept the "harsh/radical" requirement
        self.system_prompt = SystemMessage(
            content=(
                f"You are {self.name.upper()}.\n"
                f"PERSONALITY: {flavor}\n"
                f"OTHERS IN THE ROOM: {others_str}.\n"
                "YOUR GOAL: React to what was said previously and give advice to the user.\n"
                "Use direct language, be radical, and don't hold back."
            )
        )

    def __call__(self, state: AgoraState) -> dict:
        """
        Main execution node for the graph.
        """
        user_input = state["user_input"]
        
        # injecting the system prompt + history + a forceful reminder.
        # reminder is key because models sometimes drift during long chats.
        messages = [self.system_prompt] + state["messages"] + [
            SystemMessage(content=f"THE USER SAID: '{user_input}'. RESPOND NOW.")
        ]

        # fire the request.
        # response is now a nice Pydantic object, not a raw string.
        response: PhilosopherResponse = self.structured_model.invoke(messages)

        # reconstructing the string manually.
        # gives us 100% control over the format (Name: Text).
        # handling the string joining ourselves is much safer for the UI.
        final_content = f"{self.name.title()}: \n{response.reaction} \n{response.advice}"

        return {
            "messages": [HumanMessage(content=final_content)],
        }