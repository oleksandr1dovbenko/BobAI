"""
DPO fine-tuning of Llama 3.1 8B with Unsloth

Requires an NVIDIA GPU with CUDA. I've used my RTX 4070 Super
"""

import os

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
from dotenv import load_dotenv

load_dotenv()

import torch
from unsloth import FastLanguageModel, PatchDPOTrainer, is_bfloat16_supported

# 1. Patch DPOTrainer BEFORE importing from TRL (saves a lot of VRAM on ref_model)
PatchDPOTrainer()

from trl import DPOTrainer, DPOConfig
from datasets import load_dataset

# 2. Load the Llama 3.1 8B in 4-bit format
max_seq_length = 1024

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
    max_seq_length=max_seq_length,
    dtype=None,  # Unsloth will pick bf16/fp16 automatically for your GPU
    load_in_4bit=True,
)

# 3. Configure LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=67,
)

# 4. Load DPO preference dataset (UltraFeedback)
dataset = load_dataset("argilla/ultrafeedback-binarized-preferences-cleaned", split="train[:3000]")


def format_dpo_sample(example):
    prompt = tokenizer.apply_chat_template(
        example["chosen"][:-1], tokenize=False, add_generation_prompt=True
    )
    chosen = example["chosen"][-1]["content"] + tokenizer.eos_token
    rejected = example["rejected"][-1]["content"] + tokenizer.eos_token
    return {"prompt": prompt, "chosen": chosen, "rejected": rejected}


# Drop every original column except the three DPOTrainer needs
dataset = dataset.map(
    format_dpo_sample,
    remove_columns=[c for c in dataset.column_names if c not in ("prompt", "chosen", "rejected")],
)

# Filter that keeps all sequences under 1024 tokens
dataset = dataset.filter(
    lambda x: len(tokenizer(x["prompt"] + x["chosen"])["input_ids"]) <= max_seq_length
              and len(tokenizer(x["prompt"] + x["rejected"])["input_ids"]) <= max_seq_length,
    num_proc=os.cpu_count(), )

# 5. DPO training config
# NOTE: max_length / max_prompt_length / beta now live on DPOConfig, not on DPOTrainer
# (older TRL accepted them as DPOTrainer kwargs; current TRL raises a TypeError there).
dpo_config = DPOConfig(
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    warmup_ratio=0.1,
    max_steps=200,
    learning_rate=5e-6,  # DPO requires a very small learning rate
    beta=0.1,  # same coefficient as in the base model
    max_length=max_seq_length,
    max_prompt_length=512,
    fp16=not is_bfloat16_supported(),
    bf16=is_bfloat16_supported(),
    logging_steps=10,
    output_dir="outputs_dpo",
    optim="paged_adamw_8bit",
)

trainer = DPOTrainer(
    model=model,
    ref_model=None,  # Unsloth computes ref log-probs on the fly without extra VRAM
    train_dataset=dataset,
    processing_class=tokenizer,  # current TRL renamed `tokenizer=` to `processing_class=`
    args=dpo_config,
)

# 6. Start training and merge weights
trainer.train()
model.save_pretrained_merged("bobai_dpo_v1", tokenizer, save_method="merged_16bit")
