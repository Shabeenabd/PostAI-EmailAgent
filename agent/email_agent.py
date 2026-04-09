"""
AI Email Agent — core agent using LangChain + ollama.
Handles intent parsing, email drafting, refinement, and dispatch.
"""
import logging

from langchain_classic.agents import create_tool_calling_agent, AgentExecutor  
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .prompt_template import SYSTEM_PROMPT

from tools.email_tools import (
    draft_email_tool,
    refine_email_tool,
    send_email_tool,
    list_drafts_tool,
    schedule_email_tool,
    delete_draft_tool
)

logger = logging.getLogger(__name__)

def build_agent(model) -> AgentExecutor:
    """Construct and return the LangChain agent executor."""
    llm = ChatOllama(model=model)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    tools = [
        draft_email_tool,
        refine_email_tool,
        send_email_tool,
        list_drafts_tool,
        schedule_email_tool,
        delete_draft_tool
    ]

    agent = create_tool_calling_agent(llm=llm, prompt=prompt, tools=tools,)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=6,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )
