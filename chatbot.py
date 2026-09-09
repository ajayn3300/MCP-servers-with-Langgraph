from dotenv import load_dotenv
load_dotenv()
import yfinance as yf

from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List, Literal
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient


#model
llm  = ChatGroq(model="openai/gpt-oss-20b")

# intializing client
client = MultiServerMCPClient({
    'STOCKS' : {'transport':'stdio', 'command':'C:/Users/ajayn/AppData/Local/Programs/Python/Python311/python.exe', 'args':['D:/WORK/MCP/stock_MCP.py']},
    'YT_CMNTS' : {'transport':'stdio', 'command':'C:/Users/ajayn/AppData/Local/Programs/Python/Python311/python.exe', 'args':['D:/WORK/MCP/YT_cmnts_MCP.py']}})

# modifying the build_graph function
async def build_graph():

    # mod 1 : getting tools from client and bind it to llm
    tools = await client.get_tools() 
    llm_with_tools = llm.bind_tools(tools)

    async def chat_node(state:MessagesState):
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    
    graph = StateGraph(MessagesState)
    graph.add_node("chat", chat_node)
    graph.add_node('tools', ToolNode(tools))
    

    graph.add_edge(START, 'chat')
    graph.add_conditional_edges('chat', tools_condition)
    graph.add_edge('tools','chat')
    graph.add_edge('chat', END)

    graph = graph.compile()
    return graph

async def main():
    #build graph
    chatbot = await build_graph()

    #invoke chatbot
    res = await chatbot.ainvoke({'messages':HumanMessage('this is the youtube video link of a product, tell me all the goods and bads about this product,  what peoples are saying by reading the comments on this video link : https://www.youtube.com/watch?v=h3M9phIriT4 ')})

    print(res['messages'][-1].content)


#run
if __name__=='__main__':
    asyncio.run(main())