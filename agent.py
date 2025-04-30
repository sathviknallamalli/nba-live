import requests
from bs4 import BeautifulSoup
from langchain.agents import Tool, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models import ChatOpenAI
from langchain.agents import format_to_openai_tool_messages
from langchain.agents import OpenAIToolsAgentOutputParser
from langchain.tools import SerpAPIWrapper
from langchain.tools import BaseTool
from dotenv import load_dotenv
from game_utils import (
    extract_team_name_from_query,
    extract_player_name_from_query
)



__all__ = ["agent_executor"]