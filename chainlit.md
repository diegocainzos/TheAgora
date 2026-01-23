# <img src="public/favicon.png" width="40" height="40" valign="middle"> The Agora.

> "I didn't build a chatbot. I built a stage for history's sharpest tongues to settle your scores."

![Status](https://img.shields.io/badge/Status-Insanely_Great-black?style=for-the-badge) 

### The Stack
<p align="center">
  <img src="public/langgraph.png" width="100" title="LangGraph" style="vertical-align: middle; margin: 0 10px;" />
  <img src="https://cdn.worldvectorlogo.com/logos/postgresql.svg" width="100" title="PostgreSQL" style="vertical-align: middle; margin: 0 10px;" />
  <img src="public/gemini.png" width="100" title="Google Gemini" style="vertical-align: middle; margin: 0 10px;" />
  <img src="public/chainlit.png" width="100" title="Chainlit" style="vertical-align: middle; margin: 0 10px;" />
</p>

---

### The Vision
Most AI is polite. It’s servile. It’s **boring**. I find that offensive to the human spirit.

I wanted to see if I could resurrect the greatest minds in history, strip away the academic dust, and put them in a digital room to debate. **The Agora** isn't here to heal you; it's here to roast you. It’s a showcase of complex **Agent Orchestration**—proving that even as a junior developer, I can control a multi-agent collision of worldviews—focused entirely on your daily grievances.

---

### The Architecture: Craftsmanship

I care about the back of the cabinet. I rejected the spaghetti code of standard chatbots for a deterministic flow of chaos.

* **Orchestration:** `LangGraph` for state-managed multi-agent flows.
* **Interface:** `Chainlit` for a clean, minimalist experience.
* **Intelligence:** `Google Gemini Flash Lite`.
* **Persistence:** `Neon (PostgreSQL)` via `AsyncPostgresSaver` for cloud-ready session memory.
* **Structure:** `Pydantic` to enforce strictly typed JSON objects.



---

### The Cast

The Agora features custom avatars for each thinker, located in `public/avatars/`:

| <img src="public/avatars/nietzsche.png" width="50"><br>Nietzsche | <img src="public/avatars/camus.png" width="50"><br>Camus | <img src="public/avatars/sartre.png" width="50"><br>Sartre | <img src="public/avatars/hegel.png" width="50"><br>Hegel | <img src="public/avatars/kant.png" width="50"><br>Kant | <img src="public/avatars/plato.png" width="50"><br>Plato |
|:---:|:---:|:---:|:---:|:---:|:---:|

---

### File Structure: The Design

* **`philosopher.py`**: The Soul.
    * Contains the `Philosopher` class and `Pydantic` schemas (`PhilosopherResponse`).
* **`test2.py`**: The Body.
    * Manages `Chainlit` lifecycle, UI widgets, and the dynamic `StateGraph`.

---

### Getting Started

#### 1. Environment
Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:pass@endpoint.neon.tech/neondb
LANGGRAPH_DATABASE_URL=postgresql://user:pass@endpoint.neon.tech/neondb
GOOGLE_API_KEY=your_key_here
CHAINLIT_AUTH_SECRET=your_secret
CHAINLIT_USER=admin
CHAINLIT_PASS=admin

#### 2. Environment
Create a `.env` file in the root directory.

```env
DATABASE_URL=postgresql://user:pass@endpoint.neon.tech/neondb
LANGGRAPH_DATABASE_URL=postgresql://user:pass@endpoint.neon.tech/neondb
GOOGLE_API_KEY=your_key_here
CHAINLIT_AUTH_SECRET=your_generated_secret
CHAINLIT_USER=admin
CHAINLIT_PASS=admin