# agentset-gradio-demo

A Gradio app for document ingestion and Q&A using Agentset and OpenAI.

## Quick Start

### Option 1: Run from source (Recommended)

```bash
git clone https://github.com/Enes830/testagentset.git
cd testagentset/agentset-gradio-demo

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Run the app
python agentset_gradio_demo/app.py
```

The app will be available at `http://127.0.0.1:7860`

### Option 2: Using CLI command

After installing, you can also run:

```bash
agentset-gradio-demo
```

## Features

- **Chat Interface**: Ask questions and get RAG-powered responses from your documents
- **Document Ingestion**: Add documents via text, URL, or file upload
- **Job Status Tracking**: Monitor ingestion job progress
- **Configurable Settings**: Adjust OpenAI model, retrieval parameters, and more

## Requirements

- Python 3.9+
- [Agentset](https://agentset.ai) API key and namespace ID
- OpenAI API key

## Configuration

You can configure the app in two ways:

1. **Environment Variables**: Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Web Interface**: Use the Configuration tab in the app to enter your API keys

### Required Configuration

| Setting | Description |
|---------|-------------|
| OpenAI API Key | Your OpenAI API key (starts with `sk-`) |
| Agentset API Key | Your Agentset API key |
| Namespace ID | Your Agentset namespace identifier |

## Usage

### 1. Configure API Keys
Navigate to the **Configuration** tab and enter your API keys, or set them in your `.env` file.

### 2. Ingest Documents
Go to the **Ingest Documents** tab to add documents to your knowledge base:
- **Text**: Paste text content directly
- **URL**: Provide a URL to a document (PDF, etc.)
- **Upload**: Upload local files (PDF, TXT, DOCX, CSV, etc.)
- **Check Status**: Monitor ingestion job progress

### 3. Chat
Use the **Chat** tab to ask questions about your ingested documents. The RAG system will retrieve relevant context and generate responses.

### 4. Adjust Settings
Fine-tune the RAG behavior with:
- **OpenAI Model**: Choose from GPT-4o, GPT-4, GPT-3.5-turbo, etc.
- **Results to retrieve (Top-K)**: Number of document chunks to retrieve (1-20)
- **Minimum relevance score**: Filter threshold for retrieved documents (0.0-1.0)

## Project Structure

```
agentset-gradio-demo/
├── agentset_gradio_demo/
│   ├── __init__.py
│   ├── app.py              # Gradio UI application
│   ├── cli.py              # CLI entry point
│   ├── config.py           # Configuration settings
│   ├── document_ingester.py # Document ingestion logic
│   └── rag_system.py       # RAG retrieval and generation
├── .env.example
├── .gitignore
├── pyproject.toml
├── readme.md
└── requirements.txt
```

## Differences from Streamlit Version

This is a Gradio-based implementation that provides the same functionality as the Streamlit version:

| Feature | Streamlit | Gradio |
|---------|-----------|--------|
| Chat Interface | `st.chat_message` | `gr.Chatbot` |
| Tabs | `st.tabs` | `gr.Tabs`/`gr.TabItem` |
| Text Input | `st.text_input` | `gr.Textbox` |
| Sliders | `st.slider` | `gr.Slider` |
| Dropdowns | `st.selectbox` | `gr.Dropdown` |
| File Upload | `st.file_uploader` | `gr.File` |
| State Management | `st.session_state` | Python class (`AppState`) |
| Sidebar | `st.sidebar` | Configuration tab |

Both versions share the same backend logic (`rag_system.py`, `document_ingester.py`, `config.py`).

## Dependencies

- `gradio>=4.0.0` - Web UI framework
- `openai>=1.0.0` - OpenAI API client
- `agentset>=0.6.4` - Agentset SDK for document retrieval
- `python-dotenv>=1.0.0` - Environment variable management
- `requests>=2.28.0` - HTTP client

