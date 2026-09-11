# MCP‑Servers with LangGraph  
*A lightweight demo of multi‑tool integration using LangGraph and MCP (Multi‑Chain Protocol)*  

---

## 📦 Overview

This repository demonstrates how to expose **Python functions as tools** via MCP servers and orchestrate them with **LangGraph** and a **Groq LLM**.  
Three main components:

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| **STOCKS MCP** | Fetches the latest price for a ticker (e.g. `AAPL`, `RELIANCE.NS`) | `stock_MCP.py` |
| **YT_CMNTS MCP** | Downloads up to 200 YouTube comments from a video URL | `YT_cmnts_MCP.py` |
| **Chatbot** | LangGraph chatbot that can call the above tools on demand | `chatbot.py` |

The demo shows a user asking the chatbot for a YouTube video link and getting a summary of the product’s pros/cons based on real comments.

---

## ⚙️ Prerequisites

| Item | Version | Install |
|------|---------|---------|
| Python | 3.11+ | `python -m venv .venv && source .venv/bin/activate` |
| pip | – | `pip install --upgrade pip` |
| Git | – | `git clone https://github.com/ajayn3300/MCP-servers-with-Langgraph.git` |

> **Note**: The code uses `mcp`, `langgraph`, `langchain_groq`, `youtube-comment-downloader`, `yfinance`, and `python-dotenv`.  
> All dependencies are listed below.

---

## 📦 Installation

```bash
# 1. Clone the repo
git clone https://github.com/ajayn3300/MCP-servers-with-Langgraph.git
cd MCP-servers-with-Langgraph

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

If you don’t have a `requirements.txt` yet, create one with:

```text
python-dotenv
yfinance
langchain-groq
langgraph
mcp
youtube-comment-downloader
```

---

## ⚡️ Running the Demo

### 1️⃣ Set Up Environment Variables

Create a `.env` file in the repo root:

```dotenv
GROQ_API_KEY=your_groq_api_key_here
```

> The chatbot uses `langchain_groq.ChatGroq` which requires a Groq API key.

### 2️⃣ Start the Chatbot

The chatbot will automatically spawn both MCP servers as subprocesses (using `stdio` transport).

```bash
python chatbot.py
```

You should see output similar to:

```text
Chatbot: ...
```

### 3️⃣ Example Interaction

The demo code already contains an example call:

```python
res = await chatbot.ainvoke({
    'messages': HumanMessage(
        'this is the youtube video link of a product, tell me all the goods and bads about this product,  what peoples are saying by reading the comments on this video link : https://www.youtube.com/watch?v=h3M9phIriT4 '
    )
})
print(res['messages'][-1].content)
```

The chatbot will:

1. Detect that the user wants to fetch YouTube comments.  
2. Call the `yt_cmnt_downloader` tool.  
3. Pass the comments to the LLM.  
4. Return a summarized answer.

---

## 🧩 Architecture

```
┌───────────────────────┐
│  LangGraph Chatbot    │
│  ├─ chat_node          │
│  ├─ tool_node          │
│  └─ conditional edges │
└────────────┬──────────┘
             │
             ▼
┌───────────────────────┐
│  MCP Client (multi‑server) │
│  ├─ STOCKS server (stdio)  │
│  └─ YT_CMNTS server (stdio)│
└───────────────────────┘
```

- **MCP Servers** expose Python functions as *tools* that can be invoked by the LLM.  
- **LangGraph** orchestrates the flow:  
  - `chat_node` runs the LLM.  
  - `tools_condition` decides whether a tool call is needed.  
  - `ToolNode` executes the tool and returns the result.  
- The **client** (`MultiServerMCPClient`) manages connections to each server via `stdio`.

---

## 🛠️ Libraries & Tools

| Library | Purpose |
|---------|---------|
| `mcp.server.fastmcp` | Lightweight server implementation for exposing tools |
| `langchain_groq.ChatGroq` | Groq LLM wrapper |
| `langgraph` | Graph‑based orchestration of LLM and tools |
| `youtube-comment-downloader` | Fetch YouTube comments |
| `yfinance` | Retrieve stock market data |
| `python-dotenv` | Load environment variables |

---

## 📄 File Breakdown

### `stock_MCP.py`

```python
from mcp.server.fastmcp import FastMCP
import yfinance as yf

mcp = FastMCP('STOCKS')

@mcp.tool()
def get_stock_price(ticker: str) -> float | None:
    """Fetches the latest closing/current market price for a given ticker symbol."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if not data.empty:
            return round(data['Close'].iloc[-1], 2)
        info = stock.info
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        return round(price, 2) if price else None
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

- Exposes `get_stock_price` as a tool.  
- Uses `yfinance` to fetch data.

### `YT_cmnts_MCP.py`

```python
from youtube_comment_downloader import YoutubeCommentDownloader
from itertools import islice
from mcp.server.fastmcp import FastMCP

mcp = FastMCP('YT_CMNTS')

@mcp.tool()
def yt_cmnt_downloader(link: str) -> list:
    """Takes a YouTube link and returns up to 200 comments."""
    downloader = YoutubeCommentDownloader()
    comments = downloader.get_comments_from_url(link)
    comments = [c['text'] for c in islice(comments, 200)]
    return comments

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

- Exposes
PS D:\WORK\MCP> & C:\Users\ajayn\AppData\Local\Programs\Python\Python311\python.exe d:/WORK/MCP/chatbot.py
# MCP‑Servers‑with‑Langgraph

**A minimal, modular example that shows how to stitch together multiple
[MCP](https://github.com/mcp-llm/mcp) servers with a single
LangGraph chatbot.**  
The project demonstrates how to expose custom Python functions as
tools, discover them automatically, and let a language model decide
when to call them.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Setup](#setup)
- [Running the MCP Servers](#running-the-mcp-servers)
- [Using the Chatbot](#using-the-chatbot)
- [Extending the System](#extending-the-system)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

The repository contains:

| File | Purpose |
|------|---------|
| `stock_MCP.py` | MCP server exposing a single tool that fetches the latest price for a ticker symbol using `yfinance`. |
| `YT_cmnts_MCP.py` | MCP server exposing a single tool that downloads up to 200 comments from a YouTube video using `youtube_comment_downloader`. |
| `chatbot.py` | A LangGraph chatbot that automatically discovers the two tools via `MultiServerMCPClient`, binds them to a Groq‑powered LLM, and routes user messages to the appropriate tool when needed. |
| `.env` (not committed) | Stores the Groq API key (`GROQ_API_KEY`) and any other secrets. |

The goal is to show how a single chatbot can orchestrate multiple
independent services without hard‑coding any tool logic into the
graph.

---

## Project Structure

```
MCP-servers-with-Langgraph/
├─ chatbot.py            # LangGraph chatbot + tool discovery
├─ stock_MCP.py          # MCP server: get_stock_price
├─ YT_cmnts_MCP.py       # MCP server: yt_cmnt_downloader
├─ requirements.txt      # Python dependencies
├─ .env.example          # Example environment file
└─ README.md
```

---

## Architecture

1. **MCP Servers**  
   Each server runs a lightweight HTTP‑style interface via `FastMCP`.  
   * `stock_MCP.py` exposes `get_stock_price(ticker)`.  
   * `YT_cmnts_MCP.py` exposes `yt_cmnt_downloader(link)`.  
   The servers are started as separate processes and communicate over
   standard I/O.

2. **Tool Discovery**  
   `MultiServerMCPClient` connects to all servers listed in the
   configuration dictionary.  
   It queries each server for its available tools and builds a
   dictionary of callable wrappers.

3. **LangGraph**  
   * The graph contains two nodes: `chat` (LLM) and `tools` (ToolNode).  
   * `chat` calls the LLM with the conversation history.  
   * `tools_condition` decides if the LLM wants to invoke a tool; if so,
     control jumps to the `tools` node.  
   * After a tool finishes, control returns to `chat`.  
   * The process ends when the LLM produces a final answer.

4. **LLM**  
   The chatbot uses the Groq `openai/gpt-oss-20b` model via
   `langchain_groq.ChatGroq`.  The model is bound to the discovered
   tools so that it can produce function calls in its responses.

---

## Dependencies

The project relies on the following Python packages:

- `langchain-core`, `langchain-groq`, `langgraph`
- `mcp-llm/mcp` (the MCP framework)
- `yfinance` (stock price retrieval)
- `youtube_comment_downloader` (YouTube comments)
- `python-dotenv` (environment variables)

Install them with:

```bash
pip install -r requirements.txt
```

Make sure the `requirements.txt` contains the exact versions used in
the original repository.

---

## Setup

1. **Clone the repo**

   ```bash
   git clone https://github.com/ajayn3300/MCP-servers-with-Langgraph.git
   cd MCP-servers-with-Langgraph
   ```

2. **Create a `.env` file**

   Copy the example file and fill in your Groq API key:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add:

   ```
   GROQ_API_KEY=your_key_here
   ```

3. **Verify the Python executable paths**

   `chatbot.py` contains hard‑coded paths to the Python interpreter and
   the server scripts.  Update them to match your environment if
   necessary.  The dictionary passed to `MultiServerMCPClient` looks
   like:

   ```python
   {
       'STOCKS': {'transport': 'stdio', 'command': 'python', 'args': ['stock_MCP.py']},
       'YT_CMNTS': {'transport': 'stdio', 'command': 'python', 'args': ['YT_cmnts_MCP.py']}
   }
   ```

   Adjust the `command` and `args` if you use a virtual environment or a
   different interpreter.

---

## Running the MCP Servers

The servers are started automatically by `chatbot.py` via the
`MultiServerMCPClient`.  If you want to run them manually:

```bash
# In one terminal
python stock_MCP.py

# In another terminal
python YT_cmnts_MCP.py
```

Both servers will listen on `stdio` and expose their tools
automatically.

---

## Using the Chatbot

Run the chatbot with:

```bash
python chatbot.py
```

You will see a prompt where you can type any natural‑language query.
Examples:

- **Stock price**

  ```
  What is the current price of AAPL?
  ```

- **YouTube comments**

  ```
  Show me comments on this video: https://www.youtube.com/watch?v=h3M9phIriT4
  ```

The LLM will decide whether to call a tool.  When a tool is invoked,
its output is appended to the conversation and the LLM continues
generating a response that incorporates the tool’s result.

---

## Extending the System

1. **Add a new MCP server**  
   - Create a new `.py` file that imports `FastMCP`.  
   - Decorate any function you want to expose with `@mcp.tool()`.  
   - Start the server with `mcp.run(transport="stdio")`.

2. **Register the server in `chatbot.py`**  
   - Update the dictionary passed to `MultiServerMCPClient`.  
   - Ensure the `command` and `args` point to the new server script.

3. **Optional – Custom Prompt**  
   The system prompt is currently hard‑coded in the graph.  To modify
   it, edit the `SystemMessage` used when initializing the LLM.

4. **Add more tools to an existing server**  
   Simply add more `@mcp.tool()` decorated functions; the client will
   discover them automatically.

---

## Contributing

Pull requests are welcome!  
Please follow these guidelines:

1. Create a feature branch from `main`.  
2. Add tests for any new functionality.  
3. Ensure `flake8` and `black` pass.  
4. Update the README if you add new tools or change the architecture.

---
