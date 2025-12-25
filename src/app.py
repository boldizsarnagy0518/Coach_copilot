"""Coach Copilot - MVP UI."""

import tempfile
from pathlib import Path
from nicegui import ui
from src.agent import chat
from src.rag import create_chat_vectorstore, load_pdf, load_text
from src.sheets import get_sheets_client, get_newest_sheet, read_sheet

chat_store = None
messages = []


def add_styles():
    ui.add_head_html("""
    <style>
        :root {
            --bg: #080808;
            --card: #101010;
            --border: #1a1a1a;
            --text: #e0e0e0;
            --muted: #555;
        }
        body { background: #050505; color: var(--text); font-family: system-ui, sans-serif; }
        .container { max-width: 800px; margin: 0 auto; padding: 1rem; background: var(--bg); min-height: 100vh; border-left: 1px solid #111; border-right: 1px solid #111; }
        .header { border-bottom: 1px solid var(--border); padding-bottom: 1rem; margin-bottom: 1rem; }
        .msg-user { background: #151515; border: 1px solid #222; border-radius: 12px 12px 2px 12px; padding: 12px 16px; margin-left: auto; max-width: 75%; }
        .msg-bot { background: var(--card); border: 1px solid var(--border); border-radius: 12px 12px 12px 2px; padding: 12px 16px; max-width: 75%; }
        .welcome { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 2rem; text-align: center; }
        .input-area { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 8px 12px; }
        .input-box { background: transparent !important; border: none !important; }
        .btn { background: #181818 !important; border: 1px solid #222 !important; border-radius: 6px !important; }
        .btn:hover { background: #252525 !important; }
        .chip { background: #181818; border: 1px solid #222; border-radius: 6px; padding: 6px 10px; font-size: 0.8rem; cursor: pointer; }
        .chip:hover { background: #252525; }
        .dim { opacity: 0.5; }
        .disclaimer { font-size: 0.65rem; color: #404040; margin-top: 1rem; }
    </style>
    """)


@ui.page("/")
def main():
    global chat_store, messages
    chat_store = create_chat_vectorstore()
    messages = []

    ui.dark_mode().enable()
    add_styles()

    with ui.column().classes("container"):
        with ui.row().classes("header w-full items-center justify-between"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("fitness_center", size="xs").classes("dim")
                ui.label("Coach").classes("font-medium")
            ui.label("Powerlifting Copilot").classes("text-xs text-[#444]")
            with ui.row().classes("items-center gap-1 cursor-pointer"):
                ui.icon("play_circle", size="xs", color="red").classes("dim")
                ui.link(
                    "My YouTube Channel",
                    "https://www.youtube.com/@boldinagy",
                    new_tab=True,
                ).classes(
                    "text-xs text-[#888] no-underline hover:text-[#bbb] font-medium"
                )

        msg_container = ui.column().classes("w-full flex-grow py-4 gap-3")

        with msg_container:
            with ui.column().classes("welcome"):
                ui.label("Ask me anything").classes("text-lg mb-1")
                ui.label("Training, calculations, or questions").classes(
                    "text-sm text-[#555] mb-4"
                )

                with ui.row().classes("gap-2 justify-center flex-wrap"):
                    ui.label("Calculate IPF points").classes("chip").on(
                        "click",
                        lambda: fill_and_send(
                            "IPF points 600 total 83kg male",
                            msg_input,
                            msg_container,
                        ),
                    )
                    ui.label("Load plates").classes("chip").on(
                        "click",
                        lambda: fill_and_send(
                            "What plates for 180kg?", msg_input, msg_container
                        ),
                    )
                    ui.label("My training").classes("chip").on(
                        "click",
                        lambda: fill_and_send(
                            "What does my latest training sheet show?",
                            msg_input,
                            msg_container,
                        ),
                    )

                ui.label(
                    "This assistant can make mistakes. Verify important decisions with your coach."
                ).classes("disclaimer")

        with ui.row().classes("input-area w-full items-center gap-2 mt-4"):
            upload = (
                ui.upload(
                    on_upload=lambda e: handle_upload(e, msg_container),
                    auto_upload=True,
                )
                .props('flat dense accept=".pdf,.txt,.md"')
                .style("display: none")
            )
            ui.button(
                icon="attach_file", on_click=lambda: upload.run_method("pickFiles")
            ).classes("btn").props("flat dense")
            msg_input = (
                ui.input(placeholder="Message...")
                .classes("flex-grow input-box")
                .props("borderless dense")
            )
            ui.button(
                icon="arrow_upward", on_click=lambda: send(msg_input, msg_container)
            ).classes("btn").props("flat dense")

        msg_input.on("keydown.enter", lambda: send(msg_input, msg_container))


async def fill_and_send(text, input_field, container):
    input_field.value = text
    await send(input_field, container)


async def handle_upload(e, container):
    global chat_store
    content = e.content.read()
    name = e.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(name).suffix) as f:
        f.write(content)
        temp_path = f.name

    try:
        if name.endswith(".pdf"):
            docs = load_pdf(temp_path)
        else:
            text = content.decode("utf-8")
            docs = load_text(text, source=name)
        chat_store.add_documents(docs)
        with container:
            ui.label(f"+ {name}").classes("text-xs text-[#555]")
    finally:
        Path(temp_path).unlink(missing_ok=True)


async def send(input_field, container):
    global messages, chat_store
    text = input_field.value.strip()
    if not text:
        return

    input_field.value = ""
    # Add to UI-only list first (for display, though we rebuild history for LLM below)
    # Actually, we need to store persistence for history

    with container:
        with ui.column().classes("msg-user w-full items-end"):
            ui.label(text).classes("text-sm")

    with container:
        thinking = ui.row().classes("items-center gap-2")
        with thinking:
            ui.spinner(size="sm").classes("dim")

    try:
        sheets_context = ""
        if "training" in text.lower() or "sheet" in text.lower():
            spreadsheet = get_sheets_client()
            if spreadsheet:
                newest = get_newest_sheet(spreadsheet)
                data = read_sheet(spreadsheet, newest)
                if data:
                    sheets_context = (
                        f"\n\nTraining data from {newest}:\n{str(data[:10])}"
                    )

        # Convert simple dict messages to LangChain format for history
        # Note: 'messages' global variable stores dicts like {'role': 'user', 'content': '...'}
        history_objects = []
        for msg in messages:
            if msg["role"] == "user":
                history_objects.append(("human", msg["content"]))
            else:
                history_objects.append(("ai", msg["content"]))

        response = await chat(
            text + sheets_context, chat_store, chat_history=history_objects
        )

        thinking.delete()

        # Update global history
        messages.append({"role": "user", "content": text})
        messages.append({"role": "assistant", "content": response})

        with container:
            with ui.column().classes("msg-bot"):
                ui.markdown(response).classes("text-sm")
    except Exception as e:
        thinking.delete()
        with container:
            ui.label(f"Error: {e}").classes("text-sm text-red-400")

    ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")


def run():
    ui.run(title="Coach", favicon="🏋", port=8080, reload=False, show=True)


if __name__ == "__main__":
    run()
