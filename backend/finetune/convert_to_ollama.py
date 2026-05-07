"""
将 LoRA adapter 合并并转换为 Ollama 可用的 GGUF 格式。

流程:
1. 合并 LoRA adapter 到基础模型
2. 转换为 GGUF 格式（需要 llama.cpp）
3. 创建 Ollama Modelfile
4. 导入 Ollama

前置条件:
- 安装 llama.cpp（https://github.com/ggerganov/llama.cpp）
- 将 llama.cpp 目录路径设置到环境变量或命令行参数
"""

import argparse
import subprocess
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Convert LoRA model to Ollama format")
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--lora_model", type=str, default="./lora_model")
    parser.add_argument("--merge_output", type=str, default="./merged_model")
    parser.add_argument("--llama_cpp_dir", type=str, required=True,
                        help="Path to llama.cpp directory")
    parser.add_argument("--model_name", type=str, default="customer-service-v1")
    parser.add_argument("--quantize", type=str, default="q4_K_M",
                        help="GGUF quantization: q4_0, q4_K_M, q8_0, f16")
    args = parser.parse_args()

    # Step 1: Merge LoRA
    print("Step 1: Merging LoRA adapter...")
    merge_cmd = [
        sys.executable, "-c", f"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

print("Loading base model...")
model = AutoModelForCausalLM.from_pretrained(
    "{args.base_model}",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained("{args.base_model}", trust_remote_code=True)

print("Loading LoRA adapter...")
model = PeftModel.from_pretrained(model, "{args.lora_model}")

print("Merging...")
model = model.merge_and_unload()

print("Saving merged model...")
model.save_pretrained("{args.merge_output}", safe_serialization=True)
tokenizer.save_pretrained("{args.merge_output}")
print("Merge complete.")
"""
    ]
    subprocess.run(merge_cmd, check=True)

    # Step 2: Convert to GGUF
    print("\nStep 2: Converting to GGUF...")
    convert_script = os.path.join(args.llama_cpp_dir, "convert_hf_to_gguf.py")
    gguf_output = f"{args.merge_output}.gguf"

    convert_cmd = [
        sys.executable, convert_script,
        args.merge_output,
        "--outfile", gguf_output,
        "--outtype", "f16",
    ]
    subprocess.run(convert_cmd, check=True)

    # Step 3: Quantize GGUF
    print("\nStep 3: Quantizing GGUF...")
    quantize_bin = os.path.join(args.llama_cpp_dir, "llama-quantize")
    quantized_output = f"{args.merge_output}-{args.quantize}.gguf"

    quantize_cmd = [
        quantize_bin, gguf_output, quantized_output, args.quantize
    ]
    subprocess.run(quantize_cmd, check=True)

    # Step 4: Create Ollama Modelfile
    print("\nStep 4: Creating Ollama Modelfile...")
    modelfile_content = f"""
FROM {os.path.abspath(quantized_output)}
TEMPLATE \"\"\"<|im_start|>system
{{{{ .System }}}}<|im_end|>
<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
<|im_start|>assistant
\"\"\"
SYSTEM \"\"\"你是一个专业的客服助手。请根据公司的政策和知识库，准确、友好地回答用户的问题。\"\"\"
PARAMETER temperature 0.7
PARAMETER top_p 0.9
"""
    modelfile_path = os.path.join(args.merge_output, "Modelfile")
    with open(modelfile_path, "w") as f:
        f.write(modelfile_content.strip())

    print(f"\nOllama Modelfile created at: {modelfile_path}")
    print(f"\nTo import into Ollama:")
    print(f"  ollama create {args.model_name} -f {modelfile_path}")
    print(f"\nTo test:")
    print(f"  ollama run {args.model_name}")


if __name__ == "__main__":
    main()
