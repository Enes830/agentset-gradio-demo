import gradio as gr
import os
from agentset_gradio_demo.rag_system import RAGSystem
from agentset_gradio_demo.document_ingester import DocumentIngester
from agentset_gradio_demo import config

css = """
footer { display: none !important; }
span[data-testid="block-info"], .label-wrap span, label span, 
[class*="label"] span, [class*="svelte"] span { background: transparent !important; background-color: transparent !important; }
.app-header { text-align: center; padding: 24px 0 16px; border-bottom: 1px solid #e5e7eb; margin-bottom: 0; }
.app-title { font-size: 2rem !important; font-weight: 800 !important; margin: 0 !important;
    background: linear-gradient(135deg, #1a73e8 0%, #6366f1 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.chat-container { max-width: 850px; margin: 0 auto; padding: 20px 24px; }
.chat-input-area { background: #fafafa; border-radius: 16px; padding: 16px; margin-top: 16px; border: 1px solid #e5e7eb; }
.message-buttons-right, .message-buttons-left, .copy-button, .share-button, .delete-button,
button[aria-label="Share"], button[aria-label="Delete"], button[aria-label="Copy"],
.icon-button-wrapper, .icon-button { display: none !important; }
#chatbot { border: 1px solid #e5e7eb !important; border-radius: 16px !important; background: white !important; min-height: 400px; }
#chatbot .placeholder { opacity: 1 !important; }
.chat-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; 
    text-align: center; color: #64748b; padding: 40px 20px; height: 100%; }
.chat-placeholder h4 { font-size: 1.25rem; font-weight: 700; color: #1e293b; margin: 0 0 6px 0;
    background: linear-gradient(135deg, #1a73e8 0%, #6366f1 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.chat-placeholder p { font-size: 0.9rem; margin: 0 0 24px 0; max-width: 380px; line-height: 1.6; color: #64748b; }
.chat-placeholder .steps-label { font-size: 0.75rem; font-weight: 700; color: #1a73e8; margin-bottom: 12px;
    text-transform: uppercase; letter-spacing: 0.5px; }
.chat-placeholder .steps { text-align: center; font-size: 0.85rem; color: #475569; 
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); 
    padding: 16px 24px; border-radius: 12px; border: 1px solid #e2e8f0; }
.chat-placeholder .steps div { margin-bottom: 8px; line-height: 1.5; }
.chat-placeholder .steps div:last-child { margin-bottom: 0; }
.form-container { max-width: 700px; margin: 0 auto; padding: 20px; }
.result-box { min-height: auto !important; }
.result-box textarea { min-height: 36px !important; }
[role="tablist"] { justify-content: center !important; }
#chatbot details { margin-top: 12px; }
#chatbot details summary { 
    display: inline-block; padding: 6px 14px; font-size: 0.8rem; font-weight: 500;
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); 
    border: 1px solid #cbd5e1; border-radius: 8px; cursor: pointer;
    color: #475569; transition: all 0.2s ease; list-style: none;
}
#chatbot details summary::-webkit-details-marker { display: none; }
#chatbot details summary:hover { background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%); color: #1e293b; }
#chatbot details[open] summary { background: linear-gradient(135deg, #1a73e8 0%, #6366f1 100%); color: white; border-color: transparent; }
#chatbot details pre { margin-top: 10px; padding: 12px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 0.8rem; overflow-x: auto; }
"""

class AppState:
    def __init__(self):
        self.openai_api_key, self.agentset_api_key, self.agentset_namespace = \
            config.OPENAI_API_KEY or "", config.AGENTSET_API_KEY or "", config.AGENTSET_NAMESPACE_ID or ""
        self.openai_model, self.top_k, self.min_score = config.OPENAI_MODEL, config.TOP_K, config.MIN_SCORE

    def is_configured(self):
        return all([self.openai_api_key, self.agentset_api_key, self.agentset_namespace])

    def get_ingester(self):
        return DocumentIngester(self.agentset_namespace, self.agentset_api_key)

    def get_rag_system(self):
        return RAGSystem(self.agentset_namespace, self.agentset_api_key, self.openai_api_key,
                         config.SYSTEM_PROMPT, self.openai_model)

state = AppState()

def save_config(openai_key, agentset_key, namespace_id):
    state.openai_api_key, state.agentset_api_key, state.agentset_namespace = openai_key, agentset_key, namespace_id
    return "Configuration saved" if state.is_configured() else "Missing required fields"

def save_settings(model, top_k, min_score):
    state.openai_model, state.top_k, state.min_score = model, int(top_k), min_score
    return "Settings saved"


def chat(message, history):
    if not message: return history, ""
    history.append({"role": "user", "content": message})
    if not state.is_configured():
        history.append({"role": "assistant", "content": "Please configure your API keys in the Settings tab first."})
        return history, ""
    try:
        result = state.get_rag_system().query(message, top_k=state.top_k, min_score=state.min_score)
        response = result["response"]
        if ctx := result.get("context", ""):
            response += f"\n\n<details><summary> View Sources</summary>\n\n```\n{ctx[:1500]}{'...' if len(ctx) > 1500 else ''}\n```\n</details>"
        history.append({"role": "assistant", "content": response})
    except Exception as e:
        history.append({"role": "assistant", "content": f"Error: {e}"})
    return history, ""

def _handle_ingest(check_fn, action_fn):
    if not state.is_configured(): return gr.update(visible=True, value="Configure API keys first")
    if err := check_fn(): return gr.update(visible=True, value=err)
    try:
        result = action_fn()
        msg = f"Job ID: {result['job_id']}" if result["success"] else f"Error: {result['message']}"
        return gr.update(visible=True, value=msg)
    except Exception as e: return gr.update(visible=True, value=f"Error: {e}")

def ingest_text(text_content, file_name):
    return _handle_ingest(lambda: "Enter text content" if not text_content else None,
        lambda: state.get_ingester().ingest_text(text_content, file_name or None, None))

def ingest_url(doc_name, file_url):
    return _handle_ingest(lambda: "Enter document name and URL" if not doc_name or not file_url else None,
        lambda: state.get_ingester().ingest_file_from_url(doc_name, file_url, None))

def ingest_file(file, custom_name):
    return _handle_ingest(lambda: "Upload a file" if file is None else None,
        lambda: state.get_ingester().ingest_local_file(file.name, custom_name or os.path.basename(file.name), None))

def check_status(job_id):
    if not state.is_configured(): return gr.update(visible=True, value="Configure API keys first")
    if not job_id: return gr.update(visible=True, value="Enter job ID")
    try: return gr.update(visible=True, value=state.get_ingester().get_job_status(job_id)["message"])
    except Exception as e: return gr.update(visible=True, value=f"Error: {e}")


PLACEHOLDER_HTML = '''<div class="chat-placeholder">
<h4>Welcome to Agentset Gradio Demo</h4>
<p>Ask questions and get answers based on your ingested documents.</p>
<div class="steps-label">Quick start:</div>
<div class="steps">
<div>Configure your API keys in the sidebar</div>
<div>Ingest documents in the "Ingest Documents" tab</div>
<div>Start asking questions below</div>
</div>
</div>'''

def create_chat_interface():
    with gr.Column(elem_classes=["chat-container"]):
        chatbot = gr.Chatbot(elem_id="chatbot", show_label=False, height=400, placeholder=PLACEHOLDER_HTML)
        with gr.Column(elem_classes=["chat-input-area"]):
            with gr.Row():
                msg = gr.Textbox(placeholder="Type your question here...", show_label=False,
                                 container=False, scale=8, lines=1, max_lines=4, autofocus=True)
                send = gr.Button("Send", scale=1, variant="primary", size="lg")
            clear = gr.Button("Clear conversation", size="sm", variant="secondary")
        
        msg.submit(chat, [msg, chatbot], [chatbot, msg])
        send.click(chat, [msg, chatbot], [chatbot, msg])
        clear.click(lambda: ([], ""), [], [chatbot, msg])


def create_ingest_interface():
    result_box = lambda lbl="Result": gr.Textbox(label=lbl, interactive=False, elem_classes=["result-box"], lines=1, visible=False)
    with gr.Column(elem_classes=["form-container"]):
        gr.Markdown("## Ingest Documents\nAdd documents to your knowledge base for AI-powered search and retrieval.")
        with gr.Tabs(elem_classes=["inner-tabs"]):
            with gr.Tab("Text"):
                txt_content = gr.Textbox(label="Content", lines=5, placeholder="Paste your text content here...")
                with gr.Row():
                    txt_name = gr.Textbox(label="File name (optional)", placeholder="my-document.txt", scale=2)
                    txt_btn = gr.Button("Ingest Text", variant="primary", scale=1)
                txt_out = result_box()
                txt_btn.click(ingest_text, [txt_content, txt_name], txt_out)
            with gr.Tab("URL"):
                with gr.Row():
                    url_name = gr.Textbox(label="Document name", placeholder="My Document")
                    url_input = gr.Textbox(label="URL", placeholder="https://example.com/document.pdf")
                with gr.Row():
                    url_out = result_box()
                    url_btn = gr.Button("Ingest from URL", variant="primary")
                url_btn.click(ingest_url, [url_name, url_input], url_out)
            with gr.Tab("Upload"):
                with gr.Row():
                    file_input = gr.File(label="Choose a file")
                    file_name = gr.Textbox(label="Custom name (optional)", placeholder="custom-filename.pdf")
                with gr.Row():
                    file_out = result_box()
                    file_btn = gr.Button("Upload & Ingest", variant="primary")
                file_btn.click(ingest_file, [file_input, file_name], file_out)
            with gr.Tab("Check Status"):
                with gr.Row():
                    job_input = gr.Textbox(label="Job ID", placeholder="Enter the job ID...")
                    job_out = result_box("Status")
                job_btn = gr.Button("Check Status", variant="primary")
                job_btn.click(check_status, [job_input], job_out)


def create_settings_interface():
    with gr.Column(elem_classes=["form-container"]):
        gr.Markdown("## Settings\nConfigure your API keys and model preferences.")
        with gr.Tabs(elem_classes=["inner-tabs"]):
            with gr.Tab("API Configuration"):
                cfg_openai = gr.Textbox(label="OpenAI API Key", type="password", value=state.openai_api_key, placeholder="sk-...")
                cfg_agentset = gr.Textbox(label="Agentset API Key", type="password", value=state.agentset_api_key, placeholder="agentset_...")
                cfg_namespace = gr.Textbox(label="Namespace ID", value=state.agentset_namespace, placeholder="ns_...")
                cfg_out = gr.Textbox(show_label=False, interactive=False, visible=False, lines=1)
                cfg_btn = gr.Button("Save Configuration", variant="primary")
                cfg_btn.click(lambda *args: gr.update(visible=True, value=save_config(*args)), [cfg_openai, cfg_agentset, cfg_namespace], cfg_out)
            with gr.Tab("Model Settings"):
                set_model = gr.Dropdown(label="Model", choices=config.AVAILABLE_MODELS, value=state.openai_model)
                set_topk = gr.Slider(label="Results to retrieve (Top-K)", minimum=1, maximum=20, value=state.top_k, step=1)
                set_score = gr.Slider(label="Minimum relevance score", minimum=0.0, maximum=1.0, value=state.min_score, step=0.05)
                set_out = gr.Textbox(show_label=False, interactive=False, visible=False, lines=1)
                set_btn = gr.Button("Save Settings", variant="primary")
                set_btn.click(lambda *args: gr.update(visible=True, value=save_settings(*args)), [set_model, set_topk, set_score], set_out)

theme = gr.themes.Soft(primary_hue="blue", secondary_hue="slate", neutral_hue="slate",
                       radius_size="lg", font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"])

with gr.Blocks(title="Agentset RAG Demo") as demo:
    with gr.Tabs():
        with gr.Tab("Chat", id="chat"): create_chat_interface()
        with gr.Tab("Ingest Documents", id="ingest"): create_ingest_interface()
        with gr.Tab("Settings", id="settings"): create_settings_interface()

if __name__ == "__main__":
    demo.launch(theme=theme, css=css)
