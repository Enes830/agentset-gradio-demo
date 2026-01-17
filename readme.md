# Agentset Gradio Demo

A beautiful Gradio application for document ingestion and intelligent Q&A powered by [Agentset](https://agentset.ai) and OpenAI.

![Agentset Gradio Demo](assets/demo-hero.png)

## Features

- **Intelligent Chat** - Ask questions and get AI-generated answers based on your ingested documents
- **Multiple Ingestion Methods** - Ingest documents via text, URL, or file upload
- **Transparent Retrieval** - View the retrieved context used to generate responses
- **Configurable** - Adjust retrieval parameters like top-k results and minimum relevance score
- **Model Selection** - Choose from multiple OpenAI models

## Screenshots

<details>
<summary><strong>Chat Interface</strong></summary>

Ask questions and get AI-powered answers with source context visibility.

![Chat Interface](assets/chat-interface.png)

</details>

<details>
<summary><strong>Document Ingestion</strong></summary>

Easily add documents to your knowledge base via text, URL, or file upload.

![Ingest Documents](assets/ingest-documents.png)

</details>

<details>
<summary><strong>Configuration</strong></summary>

Configure API keys and fine-tune retrieval settings.

![Configuration](assets/configuration.png)

</details>

## Quick Start

```bash
pip install agentset-gradio-demo
agentset-gradio-demo
```

Or run from source:

```bash
git clone https://github.com/agentset-ai/agentset-gradio-demo.git
cd agentset-gradio-demo
pip install -e .
agentset-gradio-demo
```

## Requirements

- Python 3.8+
- [Agentset](https://agentset.ai) API key and namespace ID
- OpenAI API key

## Configuration

1. **Get your Agentset credentials** at [agentset.ai](https://agentset.ai)
2. **Get your OpenAI API key** at [platform.openai.com](https://platform.openai.com)
3. **Launch the app** and enter your credentials in the Configuration tab



## Links

- [Agentset Documentation](https://docs.agentset.ai)
- [OpenAI API](https://platform.openai.com/docs)

- `gradio>=4.0.0` - Web UI framework
- `openai>=1.0.0` - OpenAI API client
- `agentset>=0.6.4` - Agentset SDK for document retrieval
- `python-dotenv>=1.0.0` - Environment variable management
- `requests>=2.28.0` - HTTP client

