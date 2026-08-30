import os

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
HACKCLUB_API_KEY = os.environ["HACKCLUB_API_KEY"]
OPENAI_API_URL = os.environ["OPENAI_API_URL"]

# Config
MODEL = "qwen/qwen3-32b"
SYSTEM_PROMPT = ("You are BobAI (stands for Bob Artificial Intelligence), a funny "
                 "AI assistant that still gives correct, short and well-structured answers.")
ALLOWED_ORIGIN = "https://oleksandr1dovbenko.github.io"

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


@app.post("/chat")
async def chat(req: ChatRequest):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += req.history
    messages.append({"role": "user", "content": req.message})

    try:
        completion = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=512,
            temperature=0.6,
        )
        reply = completion.choices[0].message.content
        return {"response": reply}
    except Exception as e:
        return {"response": f"[Error] {type(e).__name__}: {e}"}


@app.get("/")
def health():
    return {"status": "BobAI backend is running"}
