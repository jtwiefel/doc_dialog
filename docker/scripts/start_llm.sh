#!/bin/bash
docker run --runtime nvidia --gpus all --ipc=host -p 8000:8000 \
  -v hf_cache:/root/.cache/huggingface \
  vllm/vllm-openai:latest \
  --model hugging-quants/Meta-Llama-3.1-8B-Instruct-GPTQ-INT4 \
  --quantization gptq_marlin \
  --max-model-len 12000