import os
from pathlib import Path

from unsloth import FastLanguageModel
from dotenv import load_dotenv

load_dotenv()

MODEL_DIR = Path(__file__).resolve().parent.parent / "bobai_dpo_v1"

# 1. Load the trained model in 16-bit
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=str(MODEL_DIR),
    max_seq_length=1024,
    dtype=None,
    load_in_4bit=False,
)

# 2. Push to Hugging Face Hub in GGUF format
model.push_to_hub_gguf(
    "oleksandr1dovbenko/bobai_dpo_v1-GGUF",
    tokenizer,
    quantization_method="q4_k_m",
    token=os.getenv("HF_TOKEN"),
)
