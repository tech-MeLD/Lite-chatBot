"""
将导出的对话数据格式化为 Qwen2.5 训练格式。

Qwen2.5 Chat 格式:
<|im_start|>system
{system_prompt}<|im_end|>
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
{assistant_response}<|im_end|>

输出: HuggingFace datasets 格式的 JSONL，每条包含 "text" 字段。
"""

import json
import sys

SYSTEM_PROMPT = "你是一个专业的客服助手。请根据公司的政策和知识库，准确、友好地回答用户的问题。"


def format_to_qwen(data: list[dict], output_path: str):
    formatted = []

    for item in data:
        messages = item.get("messages", [])
        if len(messages) < 2:
            continue

        # Build chat format
        text = f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            text += f"<|im_start|>{role}\n{content}<|im_end|>\n"

        formatted.append({"text": text})

    with open(output_path, "w", encoding="utf-8") as f:
        for item in formatted:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Formatted {len(formatted)} examples to {output_path}")
    return len(formatted)


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "training_data.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "formatted_data.jsonl"

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    format_to_qwen(data, output_file)
