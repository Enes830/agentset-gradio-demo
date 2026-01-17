import gradio as gr
import os
from agentset_gradio_demo.rag_system import RAGSystem
from agentset_gradio_demo.document_ingester import DocumentIngester
from agentset_gradio_demo import config

css = """
#title { font-size: 2.2rem; font-weight: bold; text-align: center; margin-bottom: 0.5em; color: #2e3a59; }
#desc { font-size: 1.1rem; text-align: center; color: #6c7a92; margin-bottom: 1em; }
footer { display: none !important; }
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
            response += f"\n\n<details><summary>View Sources</summary>\n\n```\n{ctx[:1500]}{'...' if len(ctx) > 1500 else ''}\n```\n</details>"
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




def create_chat_interface():
    with gr.Column():
        chatbot = gr.Chatbot(show_label=False, height=400)
        msg = gr.Textbox(placeholder="Type your question...", show_label=False,
                         container=False, lines=1, max_lines=3, autofocus=True)
        
        msg.submit(chat, [msg, chatbot], [chatbot, msg])


def create_ingest_interface():
    result_box = lambda lbl="Result": gr.Textbox(label=lbl, interactive=False, lines=1, visible=False)
    with gr.Column():
        gr.Markdown("### Ingest Documents\nAdd documents to your knowledge base.")
        with gr.Tabs():
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
    with gr.Column():
        gr.Markdown("### Settings\nConfigure API keys and model preferences.")
        with gr.Tabs():
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

theme = gr.themes.Base(primary_hue="orange")

with gr.Blocks(title="Agentset RAG Demo", theme=theme, css=css) as demo:
    gr.Markdown("<div id='title'>Agentset RAG Demo</div>")
    gr.Markdown("<div id='desc'>Ask questions about your ingested documents.</div>")
    with gr.Tabs():
        with gr.Tab("Chat", id="chat"): create_chat_interface()
        with gr.Tab("Ingest Documents", id="ingest"): create_ingest_interface()
        with gr.Tab("Settings", id="settings"): create_settings_interface()

if __name__ == "__main__":
    demo.launch()
