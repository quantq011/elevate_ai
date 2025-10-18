# frontend/gradio_app.py
import gradio as gr
import requests

BACKEND = "http://localhost:8000/chat"

def converse(message, history):
    resp = requests.post(BACKEND, json={"message": message})
    ans = resp.json().get("answer", "No response")
    history = history + [[message, ans]]
    return "", history

with gr.Blocks() as demo:
    gr.Markdown("# 👋 Onboarding Assistant (Gradio)")
    chatbot = gr.Chatbot(height=520)
    msg = gr.Textbox(placeholder="Ask about policies, tasks…")
    clear = gr.Button("Clear")

    msg.submit(converse, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch()
