# MCP‑servers‑with‑LangGraph  

A **multi‑tool chatbot** built on **LangGraph** that can dynamically discover and invoke remote tools (MCP servers) for stock prices, YouTube comments, and GitHub repository analysis.  
The repository demonstrates how to expose Python functions as **MCP (Multi‑Client‑Protocol) servers**, aggregate their tool specifications with **`MultiServerMCPClient`**, and wire everything together in a LangGraph state‑machine.

---  

## Table of Contents  

1. [Project Overview](#project-overview)  
2. [Key Features](#key-features)  
3. [Architecture & Data Flow](#architecture--data-flow)  
4. [Repository Walk‑through](#repository-walk-through)  
   - [stock_MCP.py](#stock_mcppy)  
   - [YT_cmnts_MCP.py](#yt_cmnts_mcppy)  
   - [github_MCP.py](#github_mcppy)  
   - [chatbot.py](#chatbotpy)  
5. [Setup & Installation](#setup--installation)  
6. [Running the Chatbot](#running-the-chatbot)  
7. [Extending the System](#extending-the-system)  
8. [Environment Variables](#environment-variables)  
9. [Contributing](#contributing)  
10. [License](#license)  

---  

## Project Overview  

The goal is to showcase a **plug‑and‑play** approach where **independent Python services** expose functions via the **MCP protocol**.  
A central LangGraph‑based chatbot queries these services at runtime, automatically binding the discovered tools to the LLM.  
The example includes three concrete tools:

| Service | Purpose | Remote Function |
|---------|---------|-----------------|
| **STOCKS** | Retrieve the latest market price for a ticker symbol | `get_stock_price(ticker: str) → float | None` |
| **YT_CMNTS** | Pull up to 250 comments from a YouTube video | `yt_cmnt_downloader(link: str) → List[str]` |
| **GITHUB** | Extract all Python‑related files from a public GitHub repo | `extract_content(repo_link: str) → Dict[str, str]` |

The chatbot can call any of these tools without hard‑coding their signatures; it discovers them via the **MCP client**.

---  

## Key Features  

- **Dynamic tool discovery** – `MultiServerMCPClient.get_tools()` fetches OpenAPI‑style tool specs from each MCP server at startup.  
- **LangGraph state‑machine** – Handles LLM messages, tool calls, and conditional routing automatically.  
- **Standard‑IO transport** – MCP servers run as lightweight subprocesses communicating over stdin/stdout, no extra networking required.  
- **Extensible design** – Adding a new MCP server only requires creating a `FastMCP` instance and decorating the function with `@mcp.tool()`.  
- **Secure secrets handling** – API keys are loaded from a `.env` file using `python-dotenv`.  

---  

## Architecture & Data Flow  

1. **MCP Servers** (`stock_MCP.py`, `YT_cmnts_MCP.py`, `github_MCP.py`)  
   - Each server creates a `FastMCP` instance, decorates a function with `@mcp.tool()`, and runs `mcp.run(transport="stdio")`.  
   - The server automatically exposes the function’s signature as a JSON‑RPC‑compatible tool definition.  

2. **Client (chatbot.py)**  
   - Instantiates a `MultiServerMCPClient` with a mapping of service names → command line to launch the corresponding server.  
   - Calls `client.get_tools()` to collect all tool specifications.  
   - Binds the tools to a Groq LLM (`ChatGroq`) using `llm.bind_tools(tools)`.  

3. **LangGraph Graph**  
   - **Nodes**:  
     - `chat` – Sends the user message to the LLM and receives a response (which may contain a tool call).  
     - `tools` – Executes the requested tool via `ToolNode`.  
   - **Edges**:  
     - START → `chat`  
     - Conditional edge from `chat` to either `tools` (if a tool call is present) or END.  
     - `tools` → `chat` (to feed the tool result back into the conversation).  

4. **Execution**  
   - The chatbot receives a user query, the LLM decides whether a tool is needed, LangGraph routes the request, the appropriate MCP server runs the function, the result is returned to the LLM, and the final answer is printed.  

---  

## Repository Walk‑through  

### `stock_MCP.py`  

- **Purpose**: Provides a single tool `get_stock_price` that returns the latest closing price for a given ticker symbol.  
- **Key Libraries**:  
  - `yfinance` – Simple interface to Yahoo Finance for historic and real‑time data.  
  - `mcp.server.fastmcp.FastMCP` – Core MCP server class.  
- **Logic Summary**:  
  1. Instantiate `FastMCP` with the service name **STOCKS**.  
  2. Decorate `get_stock_price` with `@mcp.tool()`.  
  3. Inside the function, attempt to fetch a 1‑day price history; if unavailable, fall back to `stock.info`.  
  4. Return the price rounded to two decimals, or `None` on error.  

### `YT_cmnts_MCP.py`  

- **Purpose**: Exposes `yt_cmnt_downloader` that fetches up to 250 comments from a YouTube video URL.  
- **Key Libraries**:  
  - `youtube_comment_downloader.YoutubeCommentDownloader` – Handles pagination and comment extraction.  
  - `itertools.islice` – Limits the result set to 250 items.  
  - `FastMCP` – Same MCP server base.  
- **Logic Summary**:  
  1. Create a `FastMCP` instance named **YT_CMNTS**.  
  2. Decorate the downloader function.  
  3. Use the downloader to stream comments, slice the first 250, and return a list of comment texts.  

### `github_MCP.py`  

- **Purpose**: Supplies `extract_content` which returns a dictionary mapping Python‑related file names to their source code for any public GitHub repository.  
- **Key Libraries**:  
  - `PyGithub` (`github.Github`, `github.Auth`) – Authenticated GitHub API client.  
  - `python-dotenv` – Loads `GITHUB_API_KEY` from `.env`.  
  - `FastMCP` – MCP server implementation.  
- **Logic Summary**:  
  1. Load the GitHub personal access token from environment.  
  2. Strip the base URL from the provided repo link to obtain `owner/repo`.  
  3. Use the token to instantiate an authenticated `Github` object.  
  4. Retrieve the repository, list root‑level contents, filter for `.py` and `.ipynb` files.  
  5. Decode each file’s content and assemble a `{filename: source}` dictionary.  

### `chatbot.py`  

- **Purpose**: Orchestrates the multi‑tool chatbot using LangGraph and the MCP client.  
- **Key Libraries**:  
  - `langchain_groq.ChatGroq` – LLM wrapper for Groq’s open‑source 20B model.  
  - `langgraph` – Graph‑based agent framework (`StateGraph`, `ToolNode`, `tools_condition`).  
  - `langchain_core` – Types for messages and tools.  
  - `langchain_mcp_adapters.client.MultiServerMCPClient` – Handles launching and communicating with multiple MCP servers.  
  - `dotenv` – Loads environment variables.  
  - `asyncio` – Runs the asynchronous graph.  
- **Workflow Summary**:  
  1. Load environment variables (`.env`).  
  2. Define the LLM (`ChatGroq`).  
  3. Build a `MultiServerMCPClient` with three entries, each pointing to the Python executable and the respective MCP script.  
  4. In `build_graph()`, retrieve the remote tool specs via `client.get_tools()`, bind them to the LLM, and construct a LangGraph with a chat node and a tool node.  
  5. `main()` builds the graph, sends a user message (the original request for a README), and prints the final LLM response.  

---  

## Setup & Installation  

1. **Clone the repository**  

   ```bash
   git clone https://github.com/ajayn3300/MCP-servers-with-Langgraph.git
   cd MCP-servers-with-Langgraph
   ```

2. **Create a virtual environment** (recommended)  

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # on Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**  

   ```bash
   pip install -r requirements.txt
   ```

   *If a `requirements.txt` is not present, the core packages are:*  

   - `python-dotenv`  
   - `yfinance`  
   - `langchain-groq`  
   - `langgraph`  
   - `langchain-core`  
   - `langchain-mcp-adapters`  
   - `youtube-comment-downloader`  
   - `PyGithub`  
   - `mcp` (the MCP library providing `FastMCP`)  

4. **Configure secrets**  

   Create a `.env` file in the project root with:  

   ```
   GITHUB_API_KEY=your_github_pat_here
   ```

   The Groq model does **not** require an API key for the open‑source endpoint, but if you switch to a hosted provider, add the appropriate key (e.g., `GROQ_API_KEY`).  

---  

## Running the Chatbot  

The chatbot launches the three MCP servers as subprocesses and then starts the LangGraph agent.

```bash
python chatbot.py
```

You will see the final answer printed to the console.  
The system can be used interactively by replacing the hard‑coded `HumanMessage` in `chatbot.py` with a loop that reads from `stdin`.  

---  

## Extending the System  

### Adding a New MCP Service  

1. **Create a new Python script** (e.g., `weather_MCP.py`).  
2. Instantiate `FastMCP` with a unique service name.  
3. Decorate each function you want to expose with `@mcp.tool()`.  
4. Ensure the script ends with `mcp.run(transport="stdio")`.  

```python
# skeleton
from mcp.server.fastmcp import FastMCP

mcp = FastMCP('WEATHER')

@mcp.tool()
def get_current_weather(city: str) -> str:
    ...

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

5. **Register the service** in `chatbot.py` by adding an entry to the `MultiServerMCPClient` dictionary, pointing to the new script.  

6. **Restart the chatbot** – the new tool will be discovered automatically.  

### Customising the Graph  

- To change routing logic, modify `build_graph()` – add more nodes, change edge conditions, or incorporate memory savers (`MemorySaver`).  
- For persistent state across sessions, replace the in‑memory graph with a checkpoint‑backed version (`MemorySaver` + `SQLiteCheckpoint`).  

---  

## Environment Variables  

| Variable | Description | Required by |
|----------|-------------|-------------|
| `GITHUB_API_KEY` | Personal Access Token with `repo` scope for reading public repos. | `github_MCP.py` |
| `GROQ_API_KEY` (optional) | API key for Groq hosted endpoints. | `chatbot.py` if using a non‑open model |
| `PYTHONPATH` (optional) | If you install the MCP library locally, ensure it’s on the path. | All scripts |

---  

## Contributing  

Contributions are welcome! Please follow these steps:

1. Fork the repository.  
2. Create a feature branch (`git checkout -b feature/your‑feature`).  
3. Install the development dependencies (`pip install -r requirements-dev.txt` if provided).  
4. Write tests for new functionality (use `pytest`).  
5. Ensure all existing tests pass (`pytest`).  
6. Submit a Pull Request with a clear description of the changes.  

When adding new MCP services, include a short description in this README under **Repository Walk‑through**.

---
