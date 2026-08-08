# Unsloth must be imported before torch/transformers/trl/peft so its
# runtime patches are applied correctly.
from unsloth import FastLanguageModel
import torch

users_prompt = "Who are you?"

# Unsloth's fast paths require an NVIDIA GPU
assert torch.cuda.is_available(), "Unsloth requires a CUDA GPU; none was detected."
device = torch.device("cuda")

# 1. Load the fine-tuned model in 4-bit precision (16-bit didn't fit in 12gb VRAM)
model_path = "bobai_dpo_v1"
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_path,
    max_seq_length=1024,
    dtype=None,
    load_in_4bit=True,
)
FastLanguageModel.for_inference(model)  # Enable Unsloth's native 2x faster inference

# 2. Prepare the system and user prompt
messages = [
    {
        "role": "system",
        "content": "You are BobAI (stands for Bob Artificial Intelligence), a funny "
                   "AI assistant that still gives correct, short and well-structured answers."
    },
    {
        "role": "user",
        "content": users_prompt,
    },
]

# Apply the model's own(Llama 3.1) chat template and tokenize it
inputs = tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_tensors="pt",
    return_dict=True,
).to(device)

# 3. Generate the response
outputs = model.generate(
    input_ids=inputs["input_ids"],
    attention_mask=inputs["attention_mask"],
    max_new_tokens=256,
    temperature=0.6,
    top_p=0.9,
    do_sample=True,
    use_cache=True,
)

# Trim off the prompt tokens and decode only model's response
generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
response = tokenizer.decode(generated_tokens, skip_special_tokens=True)

print("\n=== BobAI's response ===\n")
print(response)
