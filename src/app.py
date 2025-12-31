"""Coach Copilot - MVP UI with Thinking Display and Chat Sessions."""

import json
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from nicegui import ui, app

from src.agent.runner import chat
from src.rag import create_chat_vectorstore, load_pdf, load_text, index_base_knowledge
from src.tools.sheets import (
    get_sheets_client,
    get_newest_sheet,
    read_sheet,
    list_all_spreadsheets,
    get_spreadsheet_by_name,
)
from src.config import settings

MAX_SESSIONS = 10


def get_athlete_pins() -> dict:
    """Parse athlete PINs from config."""
    try:
        return json.loads(settings.athlete_pins)
    except (json.JSONDecodeError, TypeError):
        return {}


class SessionState(BaseModel):
    """Session state for chat UI."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    chat_store: Any = None
    messages: List[Dict[str, str]] = Field(default_factory=list)
    athlete_name: str = ""
    athlete_spreadsheet: Any = None
    thinking_enabled: bool = True  # Show chain-of-thought by default

    class Config:
        arbitrary_types_allowed = True


def get_user_sessions() -> List[Dict]:
    """Get all sessions for current user."""
    return app.storage.user.get("sessions", [])


def save_session(state: SessionState):
    """Save current session to user storage."""
    sessions = get_user_sessions()

    # Find existing session or create new
    session_data = {
        "id": state.session_id,
        "name": state.messages[0]["content"][:30] + "..."
        if state.messages
        else "New Chat",
        "messages": state.messages,
        "updated_at": datetime.now().isoformat(),
    }

    # Update or append
    found = False
    for i, s in enumerate(sessions):
        if s["id"] == state.session_id:
            sessions[i] = session_data
            found = True
            break

    if not found:
        sessions.insert(0, session_data)

    # Keep only last MAX_SESSIONS
    sessions = sessions[:MAX_SESSIONS]
    app.storage.user["sessions"] = sessions


def delete_session(session_id: str):
    """Delete a session."""
    sessions = get_user_sessions()
    sessions = [s for s in sessions if s["id"] != session_id]
    app.storage.user["sessions"] = sessions


def add_styles():
    ui.add_head_html("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-body: #000000;
            --bg-sidebar: #0a0a0a;
            --bg-chat: #141414;
            --border: #222;
            --text: #e0e0e0;
            --card: #1e1e1e;
        }
        body { background: var(--bg-body); color: var(--text); font-family: 'Inter', sans-serif; margin: 0; overflow: hidden; height: 100vh; }
        
        /* Layout Structure */
        .main-layout { display: flex; width: 100vw; height: 100vh; overflow: hidden; }
        
        .sidebar { 
            width: 260px; 
            height: 100%; 
            background: var(--bg-sidebar); 
            border-right: 1px solid var(--border); 
            display: flex; 
            flex-direction: column; 
            flex-shrink: 0; 
            z-index: 20;
        }
        
        .content-wrapper { 
            flex-grow: 1; 
            height: 100%; 
            background: var(--bg-body); 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
        }
        
        .chat-area { 
            width: 100%; 
            max-width: 85%; 
            height: 100%; 
            background: var(--bg-chat); 
            display: flex; 
            flex-direction: column; 
            border-left: 1px solid var(--border);
            border-right: 1px solid var(--border);
            position: relative; 
        }
        
        .header { 
            border-bottom: 1px solid var(--border); 
            padding: 1rem 2rem; 
            background: rgba(20,20,20,0.9); 
            backdrop-filter: blur(8px); 
            z-index: 10; 
            flex-shrink: 0; 
        }
        
        /* Messages */
        .msg-container { padding: 2rem; overflow-y: auto; flex-grow: 1; display: flex !important; flex-direction: column !important; align-items: stretch !important; justify-content: flex-start !important; scroll-behavior: smooth; gap: 1rem; }
        .msg-user { background: #262626; border: 1px solid #333; color: white; border-radius: 12px 12px 2px 12px; padding: 10px 16px; align-self: flex-end; max-width: 80%; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
        .msg-bot { background: transparent; padding-left: 0; max-width: 85%; align-self: flex-start; }
        
        /* Input Area */
        .input-wrapper { padding: 2rem; background: var(--bg-chat); border-top: 1px solid var(--border); flex-shrink: 0; display: flex !important; align-items: center !important; justify-content: center !important; }
        .input-area { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 6px 6px 6px 16px; display: flex; align-items: center; transition: border-color 0.2s; box-shadow: 0 4px 12px rgba(0,0,0,0.2); width: 100%; max-width: 900px; margin: 0 auto !important; }
        .input-area:focus-within { border-color: #555; }
        .input-box { color: white !important; }
        .input-box .q-field__native { color: white !important; }
        
        /* Buttons */
        .btn-new-chat { background: #262626 !important; color: #e0e0e0 !important; border: 1px solid #333 !important; border-radius: 8px !important; text-transform: none !important; font-weight: 500 !important; box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important; transition: all 0.2s !important; }
        .btn-new-chat:hover { background: #333 !important; border-color: #555 !important; color: white !important; }
        
        .btn-send { background: #e0e0e0 !important; color: black !important; border-radius: 8px !important; min-width: 36px !important; height: 36px !important; }
        .btn-send:hover { background: white !important; transform: translateY(-1px); }
        
        .chip { background: var(--card); border: 1px solid #333; border-radius: 20px; padding: 8px 16px; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; color: #aaa; }
        .chip:hover { background: #333; color: white; border-color: #555; }
        
        /* Sidebar items */
        .session-item { padding: 10px 12px; margin-bottom: 4px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; color: #999; transition: all 0.2s; display: flex; align-items: center; justify-content: space-between; }
        .session-item:hover { background: #1a1a1a; color: white; }
        .session-item.active { background: #1f1f1f; color: white; font-weight: 500; border: 1px solid #333; }
        .session-delete { opacity: 0; color: #666; transition: all 0.2s; }
        .session-delete:hover { color: #ff5555; background: rgba(255,0,0,0.1); }
        .session-item:hover .session-delete { opacity: 1; }
        
        /* Utils */
        .dim { opacity: 0.5; }
        .welcome-text { background: linear-gradient(to right, #fff, #999); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 600; font-size: 1.5rem; text-align: center; margin-bottom: 0.5rem; }
        .welcome-box { flex-grow: 1; display: flex !important; flex-direction: column !important; align-items: center !important; justify-content: center !important; width: 100%; }
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

    with ui.column().classes(
        "items-center justify-center min-h-screen w-full bg-[#050505]"
    ):
        with ui.card().classes(
            "w-[360px] p-8 bg-[#101010] border border-[#222] items-center gap-6 shadow-2xl rounded-xl"
        ):
            with ui.column().classes("items-center gap-2"):
                ui.icon("fitness_center", size="md").classes("text-[#444]")
                ui.label("COACH COPILOT").classes(
                    "font-bold text-xl tracking-wider text-gray-200"
                )
                ui.label("Athletic Intelligence Profile").classes(
                    "text-xs text-[#555] uppercase tracking-widest"
                )

            athlete = (
                ui.select(options=athlete_names, label="Select Athlete")
                .classes("w-full")
                .props("dark outlined dense behavior=menu")
            )

            pin = (
                ui.input(label="Access PIN", password=True)
                .classes("w-full")
                .props("dark outlined dense")
            )

            def verify_login():
                name = athlete.value
                if not name:
                    ui.notify("Please select an athlete", color="warning")
                    return

                correct_pin = athlete_pins.get(name)
                if pin.value == correct_pin:
                    app.storage.user["athlete_name"] = name
                    ui.navigate.to("/chat")
                else:
                    ui.notify("Invalid PIN", color="negative")

            ui.button("Initialize Session", on_click=verify_login).classes(
                "w-full text-black font-bold tracking-wide"
            ).style("background: #e0e0e0; border-radius: 8px; height: 40px;").props(
                "unelevated"
            )

            ui.label("Authorized Personnel Only").classes(
                "text-[10px] text-[#333] mt-2 font-mono"
            )


@ui.page("/chat")
@ui.page("/chat/{session_id}")
def main(session_id: str = None):
    # Check if logged in
    athlete_name = app.storage.user.get("athlete_name", "")
    if not athlete_name:
        ui.navigate.to("/")
        return

    # Load or create session
    state = SessionState()
    sessions = get_user_sessions()

    if session_id:
        # Load existing session
        for s in sessions:
            if s["id"] == session_id:
                state.session_id = s["id"]
                state.messages = s.get("messages", [])
                break

    state.chat_store = create_chat_vectorstore(state.session_id)
    state.athlete_name = athlete_name
    state.athlete_spreadsheet = get_spreadsheet_by_name(athlete_name)

    ui.dark_mode().enable()
    add_styles()

    # Main layout with sidebar
    with ui.row().classes("main-layout"):
        # Session sidebar
        # SIDEBAR
        with ui.column().classes("sidebar"):
            # New Chat Button
            ui.button("+ New Chat", on_click=lambda: ui.navigate.to("/chat")).classes(
                "w-full btn-new-chat mb-6 py-2"
            ).props("unelevated")

            ui.label("HISTORY").classes(
                "text-[10px] font-bold text-[#444] px-2 mb-2 tracking-widest"
            )

            with ui.column().classes("w-full gap-1 overflow-y-auto"):
                for s in sessions:
                    is_active = s["id"] == state.session_id
                    with ui.row().classes(
                        f"session-item {'active' if is_active else ''} w-full"
                    ):
                        ui.label(s.get("name", "Chat")[:20]).classes(
                            "flex-grow truncate"
                        ).on(
                            "click", lambda sid=s["id"]: ui.navigate.to(f"/chat/{sid}")
                        )
                        ui.button(
                            icon="close",
                            on_click=lambda sid=s["id"]: (
                                delete_session(sid),
                                ui.navigate.to("/chat"),
                            ),
                        ).props("flat dense round size=xs").classes("session-delete")

            ui.space()
            with ui.row().classes(
                "items-center gap-3 px-2 py-4 border-t border-[#222]"
            ):
                ui.avatar(icon="person", size="sm", color="#222", text_color="white")
                with ui.column().classes("gap-0"):
                    ui.label(athlete_name).classes("text-sm font-medium text-gray-300")
                    ui.label("Athlete").classes("text-[10px] text-gray-600")

        # CHAT AREA
        with ui.column().classes("content-wrapper"):
            with ui.column().classes("chat-area"):
                # Header
                with ui.row().classes("header w-full items-center justify-between"):
                    with ui.row().classes("items-center gap-3"):
                        ui.icon("fitness_center", size="xs").classes("text-[#666]")
                        ui.label("Coach Copilot").classes(
                            "font-medium text-lg tracking-tight"
                        )
                        ui.badge("v1.0", color="#222", text_color="#888").props(
                            "outline"
                        )

                    with ui.row().classes(
                        "items-center gap-2 cursor-pointer opacity-60 hover:opacity-100 transition-opacity"
                    ):
                        ui.icon("smart_display", size="xs", color="#cc0000")
                        ui.link(
                            "Coach's Channel",
                            "https://www.youtube.com/@boldinagy",
                            new_tab=True,
                        ).classes("text-xs text-gray-400 no-underline hover:text-white")

                # Messages Container
                msg_container = ui.column().classes("msg-container w-full")

                with msg_container:
                    if state.messages:
                        for msg in state.messages:
                            if msg["role"] == "user":
                                with ui.column().classes("msg-user"):
                                    ui.label(msg["content"]).classes(
                                        "text-sm leading-relaxed"
                                    )
                            else:
                                with ui.column().classes("msg-bot"):
                                    ui.markdown(msg["content"]).classes("text-sm")

                # Welcome Screen (uses same structure as input-wrapper for alignment)
                if not state.messages:
                    with (
                        ui.column()
                        .classes("input-wrapper w-full items-center justify-center")
                        .style("border-top: none; flex-grow: 1;")
                    ):
                        with (
                            ui.column()
                            .classes(
                                "input-area gap-6 text-center items-center justify-center"
                            )
                            .style(
                                "background: transparent; border: none; box-shadow: none;"
                            )
                        ):
                            ui.icon("bolt", size="xl").classes("text-[#333] mb-4")
                            ui.label(f"Ready to train, {athlete_name}?").classes(
                                "welcome-text"
                            )

                            with ui.row().classes(
                                "gap-3 justify-center flex-wrap w-full px-4"
                            ):
                                prompts = [
                                    "Calculate IPF points for 600 total @ 83kg",
                                    "What plates do I need for 180kg?",
                                    "Analyze my last deadlift session",
                                    "When is 12 weeks out from March 15?",
                                ]
                                for p in prompts:
                                    ui.label(p).classes("chip").on(
                                        "click",
                                        lambda t=p: fill_and_send(
                                            t, msg_input, msg_container, state
                                        ),
                                    )

                            ui.label(
                                "AI can make mistakes. About important decisions always consult your coach."
                            ).classes("text-[10px] text-[#333] mt-8")

                # Input Area
                with ui.column().classes(
                    "input-wrapper w-full items-center justify-center"
                ):
                    with ui.row().classes("input-area w-full gap-2"):
                        upload = (
                            ui.upload(
                                on_upload=lambda e: handle_upload(
                                    e, msg_container, state
                                ),
                                auto_upload=True,
                            )
                            .props('flat dense accept=".pdf,.txt,.md"')
                            .style("display: none")
                        )

                        ui.button(
                            icon="attach_file",
                            on_click=lambda: upload.run_method("pickFiles"),
                        ).props("flat dense round color=grey-7")

                        msg_input = (
                            ui.input(placeholder="Ask your coach...")
                            .classes("flex-grow input-box")
                            .props("borderless dense input-class='text-white'")
                        )

                        ui.button(
                            icon="arrow_upward",
                            on_click=lambda: send(msg_input, msg_container, state),
                        ).classes("btn-send").props("unelevated flat")

                    msg_input.on(
                        "keydown.enter", lambda: send(msg_input, msg_container, state)
                    )


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

    with container:
        with ui.column().classes("msg-user w-full items-end"):
            ui.label(text).classes("text-sm")

    with container:
        thinking_ui = ui.row().classes("items-center gap-2")
        with thinking_ui:
            ui.spinner(size="sm").classes("dim")
            ui.label("Thinking...").classes("text-xs text-[#555]")

    try:
        sheets_context = ""
        if "training" in text.lower() or "sheet" in text.lower():
            spreadsheet = state.athlete_spreadsheet or get_sheets_client()
            if spreadsheet:
                newest = get_newest_sheet(spreadsheet)
                data = read_sheet(spreadsheet, newest)
                if data:
                    sheets_context = f"\n\nTraining data from {newest} ({state.athlete_name}):\n{str(data[:10])}"

        # Convert messages to LangChain format
        history_objects = []
        for msg in state.messages:
            if msg["role"] == "user":
                history_objects.append(("human", msg["content"]))
            else:
                history_objects.append(("ai", msg["content"]))

        # Get response with thinking steps
        result = await chat(
            text + sheets_context,
            state.chat_store,
            chat_history=history_objects,
            include_thinking=True,
        )

        response = result["answer"]
        thinking_steps = result["thinking"]

        thinking_ui.delete()

        # Display simplified thinking summary (compact single line)
        if state.thinking_enabled and thinking_steps:
            # User-friendly translations for technical terms
            node_names = {
                "reformulate": "📝 Understanding",
                "classify": "🔍 Analyzing",
                "plan": "📋 Planning",
                "retrieve": "📚 Searching",
                "grade_documents": "⚖️ Evaluating",
                "call_agent": "🤖 Thinking",
                "tools": "🔧 Using tools",
                "generate": "✏️ Writing",
                "small_talk": "💬 Chatting",
            }
            type_names = {
                "small_talk": "quick reply",
                "command": "action",
                "complex_question": "deep search",
            }

            # Build compact flow with user-friendly names
            flow_parts = []
            for step in thinking_steps:
                friendly_name = node_names.get(step["node"], step["node"])
                if "classified_as" in step:
                    friendly_type = type_names.get(
                        step["classified_as"], step["classified_as"]
                    )
                    friendly_name += f" ({friendly_type})"
                flow_parts.append(friendly_name)

            # Show as compact inline text
            with container:
                ui.label(f"{' → '.join(flow_parts)}").classes(
                    "text-xs text-[#555] mb-1"
                )

        # Update session history
        state.messages.append({"role": "user", "content": text})
        state.messages.append({"role": "assistant", "content": response})

        # Save session
        save_session(state)

        with container:
            with ui.column().classes("msg-bot"):
                ui.markdown(response).classes("text-sm")
    except Exception as e:
        thinking_ui.delete()
        with container:
            ui.label(f"Error: {e}").classes("text-sm text-red-400")

    ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")


def run():
    print("Checking knowledge base...")
    try:
        index_base_knowledge()
    except Exception as e:
        print(f"Warning: Could not index base knowledge: {e}")

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
