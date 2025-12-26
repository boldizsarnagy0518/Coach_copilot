"""Coach Copilot - MVP UI."""

import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from nicegui import ui, app
from src.agent.runner import chat
from src.rag import create_chat_vectorstore, load_pdf, load_text
from src.tools.sheets import (
    get_sheets_client,
    get_newest_sheet,
    read_sheet,
    list_all_spreadsheets,
    get_spreadsheet_by_name,
)
from src.config import settings


def get_athlete_pins() -> dict:
    """Parse athlete PINs from config."""
    try:
        return json.loads(settings.athlete_pins)
    except (json.JSONDecodeError, TypeError):
        return {}


class SessionState(BaseModel):
    """Session state for chat UI."""

    chat_store: Any = None
    messages: List[Dict[str, str]] = Field(default_factory=list)
    athlete_name: str = ""  # Selected athlete
    athlete_spreadsheet: Any = None  # Their spreadsheet object

    class Config:
        arbitrary_types_allowed = True


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
def login_page():
    """Login page with athlete selection and PIN."""
    ui.dark_mode().enable()
    add_styles()

    # Get available athletes from spreadsheets
    spreadsheets = list_all_spreadsheets()
    athlete_names = (
        [s["name"] for s in spreadsheets] if spreadsheets else ["No athletes found"]
    )

    athlete_pins = get_athlete_pins()

    with ui.column().classes("container items-center justify-center min-h-screen"):
        with ui.column().classes("welcome max-w-sm"):
            ui.label("🏋️ Coach Copilot").classes("text-2xl font-bold mb-4")
            ui.label("Select your name and enter PIN").classes(
                "text-sm text-[#888] mb-6"
            )

            athlete_select = ui.select(
                athlete_names,
                label="Athlete",
                value=athlete_names[0] if athlete_names else None,
            ).classes("w-full mb-4")

            pin_input = ui.input(
                label="PIN", password=True, password_toggle_button=True
            ).classes("w-full mb-4")

            error_label = ui.label("").classes("text-red-400 text-sm mb-2")

            def verify_login():
                name = athlete_select.value
                pin = pin_input.value

                # Check PIN
                if name in athlete_pins:
                    if athlete_pins[name] != pin:
                        error_label.text = "Invalid PIN"
                        return
                # If no PIN configured for this athlete, allow access (coach mode)

                # Store in app storage and redirect
                app.storage.user["athlete_name"] = name
                ui.navigate.to("/chat")

            ui.button("Enter", on_click=verify_login).classes("w-full btn").props(
                "unelevated"
            )

            ui.label("No PIN? Ask your coach.").classes("text-xs text-[#444] mt-4")


@ui.page("/chat")
def main():
    # Check if logged in
    athlete_name = app.storage.user.get("athlete_name", "")
    if not athlete_name:
        ui.navigate.to("/")
        return

    state = SessionState()
    state.chat_store = create_chat_vectorstore()
    state.athlete_name = athlete_name
    state.athlete_spreadsheet = get_spreadsheet_by_name(athlete_name)

    ui.dark_mode().enable()
    add_styles()

    with ui.column().classes("container"):
        with ui.row().classes("header w-full items-center justify-between"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("fitness_center", size="xs").classes("dim")
                ui.label("Coach").classes("font-medium")
                ui.label(f"• {athlete_name}").classes("text-xs text-[#888]")
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
                            state,
                        ),
                    )
                    ui.label("Load plates").classes("chip").on(
                        "click",
                        lambda: fill_and_send(
                            "What plates for 180kg?", msg_input, msg_container, state
                        ),
                    )
                    ui.label("My training").classes("chip").on(
                        "click",
                        lambda: fill_and_send(
                            "What does my latest training sheet show?",
                            msg_input,
                            msg_container,
                            state,
                        ),
                    )

                ui.label(
                    "This assistant can make mistakes. Verify important decisions with your coach."
                ).classes("disclaimer")

        with ui.row().classes("input-area w-full items-center gap-2 mt-4"):
            upload = (
                ui.upload(
                    on_upload=lambda e: handle_upload(e, msg_container, state),
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
                icon="arrow_upward",
                on_click=lambda: send(msg_input, msg_container, state),
            ).classes("btn").props("flat dense")

        msg_input.on("keydown.enter", lambda: send(msg_input, msg_container, state))


async def fill_and_send(text, input_field, container, state: SessionState):
    input_field.value = text
    await send(input_field, container, state)


async def handle_upload(e, container, state: SessionState):
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

        if state.chat_store:
            state.chat_store.add_documents(docs)

        with container:
            ui.label(f"+ {name}").classes("text-xs text-[#555]")
    finally:
        Path(temp_path).unlink(missing_ok=True)


async def send(input_field, container, state: SessionState):
    text = input_field.value.strip()
    if not text:
        return

    input_field.value = ""
    # Add to UI-only list first (for display, though we rebuild history for LLM below)

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
            # Use athlete's specific spreadsheet
            spreadsheet = state.athlete_spreadsheet or get_sheets_client()
            if spreadsheet:
                newest = get_newest_sheet(spreadsheet)
                data = read_sheet(spreadsheet, newest)
                if data:
                    sheets_context = f"\n\nTraining data from {newest} ({state.athlete_name}):\n{str(data[:10])}"

        # Convert simple dict messages to LangChain format for history
        history_objects = []
        for msg in state.messages:
            if msg["role"] == "user":
                history_objects.append(("human", msg["content"]))
            else:
                history_objects.append(("ai", msg["content"]))

        response = await chat(
            text + sheets_context, state.chat_store, chat_history=history_objects
        )

        thinking.delete()

        # Update session history
        state.messages.append({"role": "user", "content": text})
        state.messages.append({"role": "assistant", "content": response})

        with container:
            with ui.column().classes("msg-bot"):
                ui.markdown(response).classes("text-sm")
    except Exception as e:
        thinking.delete()
        with container:
            ui.label(f"Error: {e}").classes("text-sm text-red-400")

    ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")


def run():
    ui.run(
        title="Coach",
        favicon="🏋",
        port=8080,
        reload=False,
        show=True,
        storage_secret="coach_copilot_secret",
    )


if __name__ == "__main__":
    run()
