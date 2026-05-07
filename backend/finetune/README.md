# LoRA 微调管线

将客服对话数据反哺到模型，实现"越用越聪明"的数据飞轮。

## 流程图

```
用户对话 → feedbacks + messages (PostgreSQL)
    ↓
export_data.py          ← 筛选高质量对话 (rating≥4 或 点赞)
    ↓
format_data.py          ← 格式化为 Qwen2.5 Chat 模板
    ↓
train_lora.py           ← QLoRA 微调 (8GB VRAM 可运行)
    ↓
eval_model.py           ← 评估微调效果
    ↓
convert_to_ollama.py    ← 合并+转换 GGUF → 导入 Ollama
```

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 导出训练数据

从 PostgreSQL 导出高质量客服对话：

```bash
python export_data.py training_data.json
```

### 3. 格式化数据

转换为 Qwen2.5 Chat 模板格式：

```bash
python format_data.py training_data.json formatted_data.jsonl
```

### 4. 训练模型

```bash
# QLoRA (4-bit, 推荐，8GB VRAM 可运行)
python train_lora.py \
  --data formatted_data.jsonl \
  --output ./lora_model \
  --base_model Qwen/Qwen2.5-1.5B-Instruct \
  --epochs 3 \
  --batch_size 4

# 全精度 (需要更多 VRAM)
python train_lora.py --no_4bit --batch_size 2
```

### 5. 评估效果

```bash
# 查看微调模型回答
python eval_model.py --lora_model ./lora_model

# 对比基础模型 vs 微调模型
python eval_model.py --lora_model ./lora_model --compare
```

### 6. 部署到 Ollama

```bash
python convert_to_ollama.py \
  --lora_model ./lora_model \
  --llama_cpp_dir /path/to/llama.cpp \
  --model_name customer-service-v1

# 导入 Ollama
ollama create customer-service-v1 -f ./merged_model/Modelfile

# 切换到微调模型（修改 .env）
# OLLAMA_MODEL=customer-service-v1
```

## 训练配置说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--epochs` | 3 | 训练轮数，数据量少时可增至5 |
| `--batch_size` | 4 | QLoRA 下 4 约需 6GB VRAM |
| `--lr` | 2e-4 | 学习率，LoRA 推荐 1e-4 ~ 5e-4 |
| `--use_4bit` | True | QLoRA 4-bit 量化，大幅降低显存 |

## 数据飞轮最佳实践

1. **持续收集**: 保持 feedback 收集开启，积累高质量数据
2. **定期微调**: 每积累 500+ 高质量对话后微调一次
3. **A/B 测试**: 新模型上线前与原模型对比效果
4. **人工校验**: 微调数据中混入 10% 人工标注数据提升质量
5. **回滚机制**: 保留原模型，问题时可随时切换

## 注意事项

- Qwen2.5-1.5B 对中文支持良好，训练数据以中文为主
- 首次训练建议用小数据集（100条）验证流程正确性
- LoRA rank=8 对于客服场景足够，过度参数反而可能过拟合
- 训练后务必用 eval_model.py 检查模型不会产生有害回复
