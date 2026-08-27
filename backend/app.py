import os

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

# Config
# TEST WITH SMALLER MODEL TO FIT IN 2GB OF RAM
MODEL_REPO = "Qwen/Qwen2.5-0.5B-Instruct-GGUF" #"oleksandr1dovbenko/bobai_dpo_v1-GGUF"
MODEL_FILE = "qwen2.5-0.5b-instruct-q4_k_m.gguf" #"bobai_dpo_v1.Q4_K_M.gguf"
SYSTEM_PROMPT = ("You are BobAI (stands for Bob Artificial Intelligence), a funny "
                 "AI assistant that still gives correct, short and well-structured answers.")
ALLOWED_ORIGIN = "https://oleksandr1dovbenko.github.io"

llm: Llama | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm
    model_path = hf_hub_download(
        repo_id=MODEL_REPO,
        filename=MODEL_FILE,
    )
    llm = Llama(
        model_path=model_path,
        n_ctx=4096,
        n_threads=os.cpu_count(),
        chat_format="llama-3", # matches Llama 3.1's chat template
    )
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@app.post("/chat")
def chat(req: ChatRequest):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += req.history
    messages.append({"role": "user", "content": req.message})

    result = llm.create_chat_completion(
        messages=messages,
        max_tokens=512,
        temperature=0.6,
    )
    reply = result["choices"][0]["message"]["content"]
    return {"response": reply}


@app.get("/")
def health():
    return {"status": "BobAI backend is running"}
