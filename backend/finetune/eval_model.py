"""
评估微调后的模型效果。

比较基础模型和微调模型的回答质量。
"""

import argparse
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

TEST_QUESTIONS = [
    "如何申请退货？",
    "配送大概需要多长时间？",
    "你们的客服工作时间是什么时候？",
    "支持哪些支付方式？",
    "商品有质量问题怎么办？",
    "可以货到付款吗？",
    "如何修改收货地址？",
    "退货需要保留包装吗？",
]


def generate(model, tokenizer, prompt: str, max_new_tokens: int = 200) -> str:
    messages = [
        {"role": "system", "content": "你是一个专业的客服助手。"},
        {"role": "user", "content": prompt},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
        )

    response = tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True)
    return response.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--lora_model", type=str, default="./lora_model", help="Path to LoRA adapter")
    parser.add_argument("--compare", action="store_true", help="Compare base vs fine-tuned")
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)

    print("Loading fine-tuned model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(base_model, args.lora_model)

    if args.compare:
        print("\n=== Comparing Base Model vs Fine-tuned Model ===\n")
        base_only = AutoModelForCausalLM.from_pretrained(
            args.base_model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )

        for q in TEST_QUESTIONS[:3]:
            print(f"Q: {q}")
            print(f"Base:     {generate(base_only, tokenizer, q)}")
            print(f"Finetuned: {generate(model, tokenizer, q)}")
            print()
    else:
        print("\n=== Fine-tuned Model Responses ===\n")
        for q in TEST_QUESTIONS:
            response = generate(model, tokenizer, q)
            print(f"Q: {q}")
            print(f"A: {response}")
            print()


if __name__ == "__main__":
    main()
