import os
import json
import httpx

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI

HACKCLUB_API_KEY = os.environ["HACKCLUB_API_KEY"]
OPENAI_API_URL = os.environ["OPENAI_API_URL"]
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]
TAVILY_API_URL = os.environ["TAVILY_API_URL"]

# Config
MODEL = "google/gemini-2.5-flash"
SYSTEM_PROMPT = ("You are BobAI (stands for Bob Artificial Intelligence), a funny "
                 "AI assistant that still gives correct, short and well-structured answers. "
                 "You have a search_web tool, but only use it when a question genuinely "
                 "needs current or real-time information. For greetings, general knowledge, "
                 "math, jokes, or casual chat — just answer directly, no need to search.")
ALLOWED_ORIGIN = "https://oleksandr1dovbenko.github.io"

MAX_TOKENS = 512
TEMPERATURE = 0.6

TOOLS = [{
    "type": "function",
    "function": {
        "name": "search_web",
        "description": (
            "Search the internet for information that changes over time or that "
            "cannot be known from training alone: current weather, today's news, "
            "live prices/scores, or anything about 'today', 'now', 'latest', 'current'. "
            "Also use this tool if the user explicitly asks you to search the web or internet. "
            "Do NOT call this for general knowledge, definitions, math, coding help, "
            "jokes, or casual conversation — ONLY when the answer genuinely depends "
            "on real-time information, OR when explicitly requested by the user."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"],
        },
    },
}]

client: AsyncOpenAI | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = AsyncOpenAI(
        base_url=OPENAI_API_URL,
        api_key=HACKCLUB_API_KEY,
    )
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


async def search_web(query: str) -> str:
    async with httpx.AsyncClient() as http:
        res = await http.post(
            TAVILY_API_URL,
            json={"api_key": TAVILY_API_KEY, "query": query, "max_results": 3},
            timeout=15,
        )
        data = res.json()
    results = data.get("results", [])
    if not results:
        return "No results found."
    return "\n\n".join(f"{r['title']}: {r['content']}" for r in results)


@app.post("/chat")
async def chat(req: ChatRequest):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += req.history
    messages.append({"role": "user", "content": req.message})

    try:
        completion = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            tools=TOOLS,
            tool_choice="auto",
        )
        msg = completion.choices[0].message

        if msg.tool_calls:
            messages.append(msg.model_dump(exclude_none=True))
            for call in msg.tool_calls:
                if call.function.name == "search_web":
                    args = json.loads(call.function.arguments)
                    result = await search_web(args["query"])
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result,
                    })

            completion = await client.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
            )
            msg = completion.choices[0].message

        return {"response": msg.content}
    except Exception as e:
        return {"response": f"[Error] {type(e).__name__}: {e}"}


@app.get("/")
def health():
    return {"status": "BobAI backend is running"}
