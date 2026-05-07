"""
LoRA/QLoRA 微调 Qwen2.5-1.5B-Instruct。

使用方法：
  python train_lora.py --data formatted_data.jsonl --output ./lora_model

配置说明：
  - 默认使用 4-bit 量化（QLoRA），可在 8GB VRAM GPU 上运行
  - 仅训练 LoRA adapter，基础模型权重冻结
  - 训练完成后输出 adapter 权重到 --output 目录
"""

import argparse
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
from trl import SFTTrainer


def parse_args():
    parser = argparse.ArgumentParser(description="LoRA fine-tune Qwen2.5")
    parser.add_argument("--data", type=str, default="formatted_data.jsonl", help="Training data path (JSONL)")
    parser.add_argument("--output", type=str, default="./lora_model", help="Output directory for LoRA adapter")
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct", help="Base model name or path")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Per-device batch size")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--use_4bit", action="store_true", default=True, help="Use 4-bit quantization (QLoRA)")
    parser.add_argument("--no_4bit", action="store_false", dest="use_4bit", help="Disable 4-bit quantization")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Loading data from {args.data}...")

    dataset = load_dataset("json", data_files=args.data, split="train")

    if len(dataset) == 0:
        print("ERROR: No training data found. Run export_data.py and format_data.py first.")
        return

    # Split train/val
    dataset = dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = dataset["train"]
    eval_dataset = dataset["test"]

    print(f"Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    # Load model with optional quantization
    model_kwargs = {"trust_remote_code": True}

    if args.use_4bit:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        model_kwargs["quantization_config"] = bnb_config

    print(f"Loading base model: {args.base_model}...")
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        device_map="auto",
        **model_kwargs,
    )

    # LoRA configuration
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )

    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        learning_rate=args.lr,
        warmup_ratio=0.05,
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=100,
        save_total_limit=2,
        load_best_model_at_end=True,
        bf16=True,
        report_to="none",
        remove_unused_columns=False,
    )

    # SFT Trainer (handles formatting internally)
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        peft_config=lora_config,
        dataset_text_field="text",
        max_seq_length=1024,
    )

    print("Starting training...")
    trainer.train()

    # Save LoRA adapter
    trainer.model.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)
    print(f"LoRA adapter saved to {args.output}")


if __name__ == "__main__":
    main()
