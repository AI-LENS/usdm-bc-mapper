# LLM Compatibility Guide

This guide will help you configure the tool to work with your preferred LLM provider, whether it's a commercial service, free open-source model, or self-hosted solution.

## Overview

Our system requires three essential pieces of information from any LLM provider:

1. **Base URL** - The API endpoint where your LLM service is hosted
2. **API Key** - Authentication token (not needed for self-hosted solutions)
3. **Model Name** - The specific model you want to use

All providers that expose OpenAI-compatible endpoints are supported, giving you maximum flexibility in choosing your AI solution.

## Supported Provider Categories

### 1. Commercial Providers

These are paid services that offer high-quality, managed LLM APIs.

#### OpenAI

Get your API key: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
```yaml
# config.yaml
llm_base_url: "https://api.openai.com/v1"
llm_api_key: "sk-your-openai-api-key-here"
llm_model: "gpt-5-mini"
```

#### Google Gemini

Get your API key: [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
```yaml
# config.yaml
llm_base_url: "https://generativelanguage.googleapis.com/v1beta/openai/"
llm_api_key: "your-gemini-api-key-here"
llm_model: "gemini-2.5-pro"
```

### 2. Open-Weight Models

Access powerful open-source models without managing infrastructure.

#### OpenRouter (Recommended)

OpenRouter provides free access to many open-source models and paid access to commercial ones.

Get your API key: [https://openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)
```yaml
# config.yaml
llm_base_url: "https://openrouter.ai/api/v1"
llm_api_key: "sk-or-your-openrouter-key-here"
llm_model: "meta-llama/llama-3.1-8b-instruct:free"
```

### 3. Self-Hosted Solutions
Self-hosting allows you to run language models directly on your own hardware, ensuring maximum privacy and control over your data. Before proceeding, make sure your system has adequate CPU or GPU resources to support the chosen model.

#### Ollama

After [installing](https://ollama.com/download) Ollama you can download any model from ollama [models](https://ollama.com/models)

```yaml
# config.yaml
llm_base_url: "http://localhost:11434/v1"
llm_api_key: "not-needed" # not used
llm_model: "phi4" # your downloaded model
```

#### LlamaCpp Server

```yaml
# config.yaml
llm_base_url: "http://localhost:8080/v1"
llm_api_key: "not-needed" # not used
llm_model: "your-model-name"
```

**Setup Steps:**

1. **Download LlamaCpp Server:**

   - Visit [https://github.com/ggml-org/llama.cpp/releases/](https://github.com/ggml-org/llama.cpp/releases/)
   - Find the latest release and download a build compatible with your system
   - Unzip the downloaded file to a directory of your choice

2. **Download a GGUF Model:**

   - Visit [https://huggingface.co/models?sort=trending&search=gguf](https://huggingface.co/models?sort=trending&search=gguf)
   - Choose a model that matches your system specifications (consider RAM/VRAM requirements)
   - Download the model file (e.g., `phi-4-Q4_K_M.gguf`) to a `models/` folder in your LlamaCpp directory

3. **Start the Server:**
   - Open a terminal in the directory where LlamaCpp is unzipped
   - Run the command:
   ```bash
   ./llama-server -m models/phi-4-Q4_K_M.gguf -c 2048
   ```
   - The server will start on `http://localhost:8080`

4. For more detailed documentation, visit: [https://github.com/ggml-org/llama.cpp/tree/master/tools/server](https://github.com/ggml-org/llama.cpp/tree/master/tools/server)
