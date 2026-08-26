from langchain_community.tools import DuckDuckGoSearchRun

# DuckDuckGoSearchRun is already a BaseTool
search_tool = DuckDuckGoSearchRun(region="us-en")