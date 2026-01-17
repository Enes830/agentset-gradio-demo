import gradio as gr
import os
from pathlib import Path
from rag_playground.rag_system import RAGSystem
from rag_playground.document_ingester import DocumentIngester
from rag_playground import config

# Load CSS from external file
CSS_PATH = Path(__file__).parent / "styles.css"
css = CSS_PATH.read_text() if CSS_PATH.exists() else ""


class AppState:
    def __init__(self):
        self.openai_api_key = config.OPENAI_API_KEY or ""
        self.agentset_api_key = config.AGENTSET_API_KEY or ""
        self.agentset_namespace = config.AGENTSET_NAMESPACE_ID or ""
        self.openai_model = config.OPENAI_MODEL
        self.top_k = config.TOP_K
        self.min_score = config.MIN_SCORE

    def is_configured(self):
        return all([self.openai_api_key, self.agentset_api_key, self.agentset_namespace])

    def get_ingester(self):
        return DocumentIngester(self.agentset_namespace, self.agentset_api_key)

    def get_rag_system(self):
        return RAGSystem(
            self.agentset_namespace, self.agentset_api_key,
            self.openai_api_key, config.SYSTEM_PROMPT, self.openai_model
        )


state = AppState()


def save_config(openai_key, agentset_key, namespace_id):
    state.openai_api_key, state.agentset_api_key, state.agentset_namespace = openai_key, agentset_key, namespace_id
    return "Configuration saved" if state.is_configured() else "Missing required fields"


def save_settings(model, top_k, min_score):
    state.openai_model, state.top_k, state.min_score = model, int(top_k), min_score
    return "Settings saved"


def chat(message, history):
    if not message:
        return history, ""
    history.append({"role": "user", "content": message})
    
    if not state.is_configured():
        history.append({"role": "assistant", "content": "Please configure your API keys in the Settings tab first."})
        return history, ""

    try:
        result = state.get_rag_system().query(message, top_k=state.top_k, min_score=state.min_score)
        response = result["response"]
        if ctx := result.get("context", ""):
            response += f"\n\n---\n**Sources:**\n```\n{ctx[:1500]}{'...' if len(ctx) > 1500 else ''}\n```"
        history.append({"role": "assistant", "content": response})
    except Exception as e:
        history.append({"role": "assistant", "content": f"Error: {e}"})
    return history, ""


def _handle_ingest(check_fn, action_fn):
    """Helper for ingest operations with common error handling."""
    if not state.is_configured():
        return "Configure API keys first"
    if err := check_fn():
        return err
    try:
        result = action_fn()
        return f"Job ID: {result['job_id']}" if result["success"] else f"Error: {result['message']}"
    except Exception as e:
        return f"Error: {e}"


def ingest_text(text_content, file_name):
    return _handle_ingest(
        lambda: "Enter text content" if not text_content else None,
        lambda: state.get_ingester().ingest_text(text_content, file_name or None, None)
    )


def ingest_url(doc_name, file_url):
    return _handle_ingest(
        lambda: "Enter document name and URL" if not doc_name or not file_url else None,
        lambda: state.get_ingester().ingest_file_from_url(doc_name, file_url, None)
    )


def ingest_file(file, custom_name):
    return _handle_ingest(
        lambda: "Upload a file" if file is None else None,
        lambda: state.get_ingester().ingest_local_file(file.name, custom_name or os.path.basename(file.name), None)
    )


def check_status(job_id):
    if not state.is_configured():
        return "Configure API keys first"
    if not job_id:
        return "Enter job ID"
    try:
        return state.get_ingester().get_job_status(job_id)["message"]
    except Exception as e:
        return f"Error: {e}"


def clear_chat():
    return [], ""


def create_chat_interface():
    with gr.Column(elem_classes=["chat-container"]):
        with gr.Column(elem_classes=["chat-header"]):
            gr.Markdown("# agentset-gradio-demo", elem_classes=["chat-title"])
            gr.Markdown("Ask questions about your documents using AI-powered search", elem_classes=["chat-description"])
        
        chatbot = gr.Chatbot(elem_id="chatbot", show_label=False, avatar_images=(None, None), layout="panel")
        
        with gr.Column(elem_classes=["input-section"]):
            with gr.Row(elem_classes=["input-row"]):
                msg = gr.Textbox(elem_id="msg-input", placeholder="Type your question here...", show_label=False, container=False, scale=8, lines=1, max_lines=4)
                send = gr.Button("Send", elem_id="send-btn", scale=1, variant="primary")
            clear = gr.Button("Clear conversation", elem_id="clear-btn", size="sm")
        
        msg.submit(chat, [msg, chatbot], [chatbot, msg])
        send.click(chat, [msg, chatbot], [chatbot, msg])
        clear.click(clear_chat, [], [chatbot, msg])


def _result_box():
    return gr.Textbox(label="Result", interactive=False, elem_classes=["result-box"])


def create_ingest_interface():
    with gr.Column(elem_classes=["form-container"]):
        gr.Markdown("## Ingest Documents", elem_classes=["settings-title"])
        gr.Markdown("Add documents to your knowledge base for AI-powered search and retrieval.")
        
        with gr.Tabs(elem_classes=["inner-tabs"]):
            with gr.Tab("Text"):
                txt_content = gr.Textbox(label="Content", lines=8, placeholder="Paste your text content here...")
                txt_name = gr.Textbox(label="File name (optional)", placeholder="my-document.txt")
                txt_btn = gr.Button("Ingest Text", variant="primary")
                txt_out = _result_box()
                txt_btn.click(ingest_text, [txt_content, txt_name], txt_out)

            with gr.Tab("URL"):
                url_name = gr.Textbox(label="Document name", placeholder="My Document")
                url_input = gr.Textbox(label="URL", placeholder="https://example.com/document.pdf")
                url_btn = gr.Button("Ingest from URL", variant="primary")
                url_out = _result_box()
                url_btn.click(ingest_url, [url_name, url_input], url_out)

            with gr.Tab("Upload"):
                file_input = gr.File(label="Choose a file")
                file_name = gr.Textbox(label="Custom name (optional)", placeholder="custom-filename.pdf")
                file_btn = gr.Button("Upload & Ingest", variant="primary")
                file_out = _result_box()
                file_btn.click(ingest_file, [file_input, file_name], file_out)

            with gr.Tab("Check Status"):
                job_input = gr.Textbox(label="Job ID", placeholder="Enter the job ID from ingestion...")
                job_btn = gr.Button("Check Status", variant="primary")
                job_out = gr.Textbox(label="Status", interactive=False, elem_classes=["result-box"])
                job_btn.click(check_status, [job_input], job_out)


def create_settings_interface():
    with gr.Column(elem_classes=["settings-container"]):
        with gr.Column(elem_classes=["settings-section"]):
            gr.Markdown("## API Configuration", elem_classes=["settings-title"])
            cfg_openai = gr.Textbox(label="OpenAI API Key", type="password", value=state.openai_api_key, placeholder="sk-...")
            cfg_agentset = gr.Textbox(label="Agentset API Key", type="password", value=state.agentset_api_key, placeholder="agentset_...")
            cfg_namespace = gr.Textbox(label="Namespace ID", value=state.agentset_namespace, placeholder="ns_...")
            cfg_btn = gr.Button("Save Configuration", variant="primary")
            cfg_out = gr.Textbox(show_label=False, interactive=False)
            cfg_btn.click(save_config, [cfg_openai, cfg_agentset, cfg_namespace], cfg_out)

        with gr.Column(elem_classes=["settings-section"]):
            gr.Markdown("## Model Settings", elem_classes=["settings-title"])
            set_model = gr.Dropdown(label="Model", choices=config.AVAILABLE_MODELS, value=state.openai_model)
            set_topk = gr.Slider(label="Results to retrieve (Top-K)", minimum=1, maximum=20, value=state.top_k, step=1)
            set_score = gr.Slider(label="Minimum relevance score", minimum=0.0, maximum=1.0, value=state.min_score, step=0.05)
            set_btn = gr.Button("Save Settings", variant="secondary")
            set_out = gr.Textbox(show_label=False, interactive=False)
            set_btn.click(save_settings, [set_model, set_topk, set_score], set_out)


# Build the main application
with gr.Blocks(title="agentset-gradio-demo") as demo:
    with gr.Tabs() as tabs:
        with gr.Tab("Chat", id="chat"):
            create_chat_interface()
        
        with gr.Tab("Ingest Documents", id="ingest"):
            create_ingest_interface()
        
        with gr.Tab("Settings", id="settings"):
            create_settings_interface()


if __name__ == "__main__":
    demo.launch(css=css, theme=gr.themes.Soft())
