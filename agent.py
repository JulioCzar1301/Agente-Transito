# Copyright 2025
# Licensed under the Apache License, Version 2.0

from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent, LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.genai import types
from prompt import DB_MCP_PROMPT
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# -------------------------
# CONFIGURAÇÃO DO AGENTE
# -------------------------

APP_NAME = "database_agent_api"
USER_ID = "user1234"
SESSION_ID = "session001"

root_agent = LlmAgent(
    name="database_ia_agent",
    model="gemini-2.0-flash",
    description="Agente que acessa banco de dados via MCP e processa com IA.",
    instruction= DB_MCP_PROMPT,
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="python",
                    args=[
                        "C:/Ambiente de Desenvolvimento/Agente-Transito/agent.py"
                    ],
                ),
                timeout=30,
            ),
        )
    ],
)

# -------------------------
# SESSION + RUNNER (igual ao exemplo)
# -------------------------

async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner

async def call_agent_async(query: str) -> str:
    content = types.Content(role="user", parts=[types.Part(text=query)])

    session, runner = await setup_session_and_runner()
    events = runner.run_async(
        user_id=USER_ID, session_id=SESSION_ID, new_message=content
    )

    async for event in events:
        if event.is_final_response():
            print("Final response received.", event.content.parts)
            return event.content.parts[0].text

    return "Nenhuma resposta final recebida."

# -------------------------
# API FASTAPI
# -------------------------

app = FastAPI(title="Database IA API (Google ADK)")

origins = [
    "http://localhost:3000", 
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],         
)

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def query_api(req: QueryRequest):
    resposta = await call_agent_async(req.query)
    return {"resposta": resposta}

@app.get("/")
def home():
    return {"status": "online", "agent": root_agent.name}