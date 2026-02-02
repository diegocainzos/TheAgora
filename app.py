import os
import ssl
import psycopg
import chainlit as cl
from dotenv import load_dotenv

# Database and LangChain imports
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.input_widget import Switch, Select
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

# Custom logic
from philosopher import Philosopher, AgoraState
from typing import Literal, List
from langchain_core.language_models import BaseChatModel

load_dotenv()

# --- GLOBALS & CONFIG ---

AVAILABLE_PHILOSOPHERS = ["nietzsche", "camus", "sartre", "hegel", "kant", "plato", "debug"]
DATABASE_URL = os.getenv("DATABASE_URL")
LANGGRAPH_DATABASE_URL = os.getenv("LANGGRAPH_DATABASE_URL")

# initialized once globally to save resources
model = init_chat_model(
    "gemini-flash-lite-latest",
    model_provider="google_genai",
    temperature=0.8,
)

@cl.data_layer
def get_data_layer():
    """
    Setup the persistence layer for Chainlit's UI history.
    Neon/Postgres requires specific SSL handling.
    """
    raw_url = DATABASE_URL
    if "?" in raw_url:
        raw_url = raw_url.split("?")[0]

    # asyncpg needs a proper ssl context object, it hates sslmode in the string
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    return SQLAlchemyDataLayer(
        conninfo=raw_url.replace("postgresql://", "postgresql+asyncpg://"),
        connect_args={"ssl": ssl_context}
    )

# --- GRAPH ORCHESTRATION ---

def graph_builder(selected_names: List[str], model: BaseChatModel, rounds: int):
    if not selected_names:
        return None

    # messages limit = (philosophers * loops) + 1 (the user message)
    limit = (len(selected_names) * rounds) + 1

    def dynamic_moderator(state: AgoraState) -> Literal["continue", "end"]:
        # purely message count based for now
        if len(state["messages"]) >= limit:
            return "end"
        return "continue"

    builder = StateGraph(AgoraState)
    
    # spawning agent instances
    philosophers_instances = [
        Philosopher(name=n, model=model, participants=selected_names)
        for n in selected_names
    ]

    for p in philosophers_instances:
        builder.add_node(p.name, p)

    builder.add_edge(START, philosophers_instances[0].name)

    # linking them 1 by 1
    for i in range(len(philosophers_instances) - 1):
        builder.add_edge(
            philosophers_instances[i].name, philosophers_instances[i + 1].name
        )

    # last one loops back or finishes
    last_phil = philosophers_instances[-1].name
    builder.add_conditional_edges(
        last_phil, 
        dynamic_moderator, 
        {"continue": philosophers_instances[0].name, "end": END}
    )
    
    # pull the saver we initialized in on_chat_start
    checkpoint = cl.user_session.get("saver")
    return builder.compile(checkpointer=checkpoint)


async def update_graph_session(selected_names: List[str], rounds: int):
    """Refreshes the runnable graph in the user session."""
    if len(selected_names) < 2:
        await cl.Message(content="⚠️ Choose at least 2 philosophers.").send()
        cl.user_session.set("runnable_graph", None)
        return
    
    new_graph = graph_builder(selected_names, model, rounds)
    cl.user_session.set("runnable_graph", new_graph)
    
    # names_txt = ", ".join([n.title() for n in selected_names])
    # await cl.Message(
    #     content=f"✅ Session updated: {names_txt} ({rounds} Rounds)"
    # ).send()


# --- EVENT HANDLERS ---

@cl.on_chat_start
async def start():
    # langgraph persistence setup
    conn = await psycopg.AsyncConnection.connect(LANGGRAPH_DATABASE_URL, autocommit=True)
    saver = AsyncPostgresSaver(conn)
    await saver.setup() # making sure tables exist in Neon
    
    # keeping conn in session to close it later
    cl.user_session.set("db_conn", conn)
    cl.user_session.set("saver", saver)
    
    defaults = ["nietzsche", "camus", "sartre"]
    
    # building the UI sidebar widgets
    settings_widgets = [
        Select(
            id="Rounds",
            label="Rounds (Loops)",
            values=["1", "2", "3"],
            initial_index=0
        )
    ]

    for phil in AVAILABLE_PHILOSOPHERS:
        settings_widgets.append(
            Switch(id=phil, label=phil.title(), initial=(phil in defaults))
        )

    await cl.ChatSettings(settings_widgets).send()
    await update_graph_session(defaults, rounds=1)

    # sending a warm and welcoming message
    welcome_message = "Welcome to the Agora. You are about to be roasted by the greatest minds in history. This is radical therapy: no excuses, no filters. Configure your philosophers in the settings (top right) and tell us: what is bothering your existence today?"
    await cl.Message(content=f"Hello {welcome_message}", author="Diego").send()
    


@cl.on_settings_update
async def setup_agent(settings):
    selected = [name for name in AVAILABLE_PHILOSOPHERS if settings.get(name, False)]
    rounds_val = int(settings.get("Rounds", "1"))
    await update_graph_session(selected, rounds_val)


@cl.on_message
async def main(message: cl.Message):
    graph = cl.user_session.get("runnable_graph")
    if not graph:
        await cl.Message(content="❌ Please configure philosophers in settings.").send()
        return
    
    config = {"configurable": {"thread_id": cl.context.session.thread_id}}

    # we pass user_input separately so agents know what to reply to
    initial_state = {
        "messages": [HumanMessage(content=message.content)], 
        "user_input": message.content 
    }

    # using astream because we have structured output + post-processing in the nodes
    # streaming tokens would just show ugly raw JSON
    async for update in graph.astream(initial_state, config=config):
        for node_name, value in update.items():
            if "messages" in value and value["messages"]:
                last_msg = value["messages"][-1]
                
                # send the final formatted string to the UI
                await cl.Message(
                    author=node_name.title(),
                    content=last_msg.content
                ).send()

@cl.on_chat_end
async def on_chat_end():
    # cleaning up database connections to avoid leaks
    conn = cl.user_session.get("db_conn")
    if conn:
        await conn.close()

