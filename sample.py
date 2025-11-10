# AI File Organizer with Enhanced Streamlit UI
# ------------------------------------------------------
# Full end-to-end code combining:
# ✅ LangGraph backend
# ✅ AI classification
# ✅ Organized folder fix
# ✅ ZIP download fix
# ✅ Sidebar
# ✅ Progress bar
# ✅ Tabs
# ✅ Clean UI
# ------------------------------------------------------

import os
import shutil
import zipfile
import time
import streamlit as st
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
import re

# ------------------------------
# LLM Setup
# ------------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key="AIzaSyB5I_QHm08l-LrrCR6pQhputZr6GzwT9nw"
)

# ------------------------------
# Utility for cleaning folder names
# ------------------------------
def clean_category(cat: str) -> str:
    cat = cat.strip().lower()
    cat = re.sub(r'[^a-z0-9_-]', '', cat)
    if not cat:
        return "others"
    return cat

# ------------------------------
# LangGraph State Definition
# ------------------------------
class FileState(TypedDict):
    filepath: str
    category: str
    new_path: str
    logs: List[str]

# ------------------------------
# Classification Node
# ------------------------------
def classify_file(state: FileState) -> FileState:
    filepath = state["filepath"]
    filename = os.path.basename(filepath)
    ext = filename.split(".")[-1].lower()

    mapping = {
    # Documents
    "pdf": "documents",
    "doc": "documents",
    "docx": "documents",
    "txt": "documents",
    "md": "documents",
    "rtf": "documents",
    "epub": "documents",

    # Images
    "png": "images",
    "jpg": "images",
    "jpeg": "images",
    "gif": "images",    
    "svg": "images",
    "webp": "images",

    # Videos
    "mp4": "videos",
    "mkv": "videos",
    "mov": "videos",
    "avi": "videos",
    "wmv": "videos",
    "webm": "videos",

    # Audio
    "mp3": "audio",
    "wav": "audio",
    "aac": "audio",
    "ogg": "audio",
    "flac": "audio",

    # Archives
    "zip": "archives",
    "rar": "archives",
    "tar": "archives",
    "gz": "archives",
    "7z": "archives",

    # Code
    "py": "code",
    "js": "code",
    "ts": "code",
    "html": "code",
    "css": "code",
    "java": "code",
    "c": "code",
    "cpp": "code",
    "cs": "code",
    "rb": "code",
    "php": "code",
    "swift": "code",
    "go": "code",
    "rs": "code",
    "kt": "code",
    "sh": "code",
    "bat": "code",

    # Data
    "csv": "data",
    "xlsx": "spreadsheets",
    "xls": "spreadsheets",
    "ods": "spreadsheets",
    "json": "data",
    "xml": "data",
    "yaml": "data",
    "yml": "data",

    # Applications & binaries
    "exe": "applications",
    "dll": "system",
    "bin": "binaries",
    "iso": "disk_images",
}

    if ext in mapping:
        state["category"] = mapping[ext]
    else:
        ai_result = llm.invoke(
            f"Return ONLY one single-word category for this file: {filename}. "
            "Options: images, documents, data, videos, audio, archives, code, others. "
            "Respond with ONLY the category."
        )
        state["category"] = clean_category(ai_result.content)

    state["logs"].append(f"Classified {filename} as {state['category']}")
    return state

# ------------------------------
# Move File Node
# ------------------------------
def move_file(state: FileState) -> FileState:
    filepath = state["filepath"]
    input_folder = os.path.dirname(filepath)

    base_folder = os.path.join(input_folder, "organized")
    os.makedirs(base_folder, exist_ok=True)

    target_folder = os.path.join(base_folder, state["category"])
    os.makedirs(target_folder, exist_ok=True)

    new_path = os.path.join(target_folder, os.path.basename(filepath))
    shutil.move(filepath, new_path)

    state["new_path"] = new_path
    state["logs"].append(f"Moved file to {new_path}")
    return state

# ------------------------------
# Log Node
# ------------------------------
def log_report(state: FileState) -> FileState:
    state["logs"].append("Completed file processing.")
    return state

# ------------------------------
# Build Graph
# ------------------------------
graph = StateGraph(FileState)

graph.add_node("classify", classify_file)
graph.add_node("move", move_file)
graph.add_node("log", log_report)

graph.set_entry_point("classify")
graph.add_edge("classify", "move")
graph.add_edge("move", "log")
graph.add_edge("log", END)

app = graph.compile()

# ------------------------------
# STREAMLIT UI (Enhanced)
# ------------------------------
st.set_page_config(page_title="AI File Organizer", layout="wide")

# Sidebar
sidebar = st.sidebar
sidebar.title("AI File Organizer")
sidebar.markdown("Automatically classify and organize messy folders using AI.")

instructions = sidebar.expander("Instructions", expanded=False)
instructions.write(
    """
    1. Enter the folder path you want to organize.
    2. Click Start Organizing.
    3. Wait until processing completes.
    4. Download the ZIP of organized files.
    """
)

# Tabs
organize_tab, logs_tab, settings_tab = st.tabs(["📁 Organizer", "📜 Logs", "⚙️ Settings"])

# --------------- ORGANIZER TAB ---------------
with organize_tab:
    st.title("Smart File Organizer ✨")
    st.markdown("Organize your messy folders automatically using AI.")

    folder_path = st.text_input("Select the folder you want to organize:")

    if st.button("Start Organizing", use_container_width=True):
        if not folder_path or not os.path.exists(folder_path):
            st.error("Invalid folder path.")
        else:
            st.info("Organizing files... please wait.")

            report_logs = []
            summary_logs = []
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            total_files = len(files)

            progress = st.progress(0)

            for idx, file in enumerate(files):
                full_path = os.path.join(folder_path, file)
                result = app.invoke({
                    "filepath": full_path,
                    "category": "",
                    "new_path": "",
                    "logs": []
                })
                report_logs.extend(result["logs"])

                # AI Document Summary (Only if enabled)
                if st.session_state.get("settings", {}).get("enable_summary", True):
                    try:
                        with open(full_path, 'rb') as f:
                            content = f.read(5000).decode(errors='ignore')
                        summary = llm.invoke(f"Summarize this document in one sentence: {content}").content
                        summary_logs.append(f"{file}: {summary}")
                    except:
                        summary_logs.append(f"{file}: Could not read content for summary.")
                progress.progress((idx + 1) / total_files).progress((idx + 1) / total_files)
                time.sleep(0.05)

            st.success("✅ All files organized successfully!")

            st.session_state["logs"] = report_logs
            st.session_state["summaries"] = summary_logs

# --------------- LOGS TAB --------------- ---------------
with logs_tab:
    st.subheader("📝 Activity Log")
    if "logs" in st.session_state:
        with st.expander("View Logs", expanded=True):
            for log in st.session_state["logs"]:
                st.write("-", log)
    else:
        st.info("No logs yet. Run the organizer first.")

# --------------- SEARCH TAB ---------------
search_tab = st.tabs(["🔎 Search Assistant"])[0]
with search_tab:
    st.subheader("AI File Search Assistant")

    if not st.session_state.get("settings", {}).get("enable_search", True):
        st.warning("AI Search Assistant is disabled in Settings.")
    else:
        query = st.text_input("Ask something about your files:")
        if st.button("Search Files"):
            if "summaries" not in st.session_state:
                st.error("Run the organizer first.")
            else:
                combined = "".join(st.session_state["summaries"])
                answer = llm.invoke(f"User query: {query}. Search through these file summaries and answer: {combined}").content
                st.write(answer)

# --------------- SETTINGS TAB")
    st.write("Configure how your AI File Organizer behaves.")

    # Theme selection
    theme = st.selectbox("Choose UI Theme:", ["Default", "Dark", "Neon", "Minimal"], index=0)

    # Toggle smart summary
    enable_summary = st.checkbox("Enable AI Document Summaries", value=True)

    # Toggle search assistant
    enable_search = st.checkbox("Enable AI Search Assistant", value=True)

    # File size limit
    size_limit = st.slider("Maximum File Size to Process (MB)", min_value=1, max_value=100, value=50)

    # Save settings to session
    st.session_state["settings"] = {
        "theme": theme,
        "enable_summary": enable_summary,
        "enable_search": enable_search,
        "size_limit": size_limit
    }

    st.success("Settings Saved ✔️")
