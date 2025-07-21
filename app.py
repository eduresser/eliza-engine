import streamlit as st
import random
import os
import json
import time
from pydantic import ValidationError
from streamlit_ace import st_ace
from eliza import Eliza

DEFAULT_SCRIPT = "Eliza"

st.set_page_config(layout="wide")

@st.cache_data
def load_templates(folder="scripts"):
    """Loads script templates from a folder."""
    templates = {}
    if not os.path.exists(folder):
        st.warning(f"Script folder '{folder}' not found.")
        return templates
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            filepath = os.path.join(folder, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    data = json.loads(content)
                    script_name = data.get("name", os.path.splitext(filename)[0])
                    templates[script_name] = content
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading template {filename}: {e}")
    return templates

def initialize_session_state():
    if "chat_started" not in st.session_state:
        st.session_state.chat_started = False
    if "eliza_bot" not in st.session_state:
        st.session_state.eliza_bot = None
    if "script_content" not in st.session_state:
        st.session_state.script_content = ""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "template_selection" not in st.session_state:
        st.session_state.template_selection = DEFAULT_SCRIPT

def render_config_screen():
    st.title("🤖 Eliza Engine Configuration")
    st.markdown("Choose a script, upload your own JSON script, or write a custom script below.")

    templates = load_templates()
    
    with st.sidebar:
        st.header("Script Options")
        source_choice = st.radio(
            "Script Source",
            ["Use a template", "Upload JSON file"],
            key="source_choice"
        )

        if source_choice == "Use a template":
            template_options = ["Custom"] + sorted(list(templates.keys()))
            
            current_selection_index = template_options.index(DEFAULT_SCRIPT) if DEFAULT_SCRIPT in template_options else 0
            if st.session_state.template_selection in template_options:
                current_selection_index = template_options.index(st.session_state.template_selection)

            selected_template = st.selectbox(
                "Select script:",
                template_options,
                index=current_selection_index,
                key="template_selector"
            )
            
            if selected_template != st.session_state.template_selection:
                st.session_state.template_selection = selected_template
                if selected_template == "Custom":
                    st.session_state.script_content = "{}"
                else:
                    st.session_state.script_content = templates[selected_template]
                st.rerun()
            elif selected_template != "Custom":
                st.session_state.script_content = templates[selected_template]

        else:
            uploaded_file = st.file_uploader(
                "Upload your .json script", type=["json"]
            )
            if uploaded_file:
                new_content = uploaded_file.getvalue().decode("utf-8")
                if new_content != st.session_state.script_content:
                    st.session_state.script_content = new_content
                    st.session_state.template_selection = "Custom"
                    st.rerun()

    edited_content = st_ace(
        value=st.session_state.script_content,
        language="json",
        theme="dracula",
        height=400,
        key="ace_editor",
        tab_size=2
    )

    if edited_content != st.session_state.script_content:
        st.session_state.script_content = edited_content
        st.session_state.template_selection = "Custom"
        st.rerun()

    if st.button("✅ Start Chat", use_container_width=True, type="primary"):
        if not st.session_state.script_content.strip():
            st.error("Script cannot be empty. Please load, select, or write a script.")
            return

        try:
            bot = Eliza(st.session_state.script_content)
            
            st.session_state.eliza_bot = bot
            st.session_state.chat_started = True
            
            initial_message = random.choice(bot.initials)
            st.session_state.messages = [{"role": "assistant", "content": initial_message}]
            
            st.rerun()
        
        except (ValidationError, json.JSONDecodeError, ValueError, KeyError) as e:
            st.error(f"❌ Error validating script:\n\n{e}")

def render_chat_screen():
    bot_name = st.session_state.eliza_bot.name
    st.title(f"Chatting with: {bot_name}")

    if st.sidebar.button("↩️ Back to Script Editor"):
        st.session_state.chat_started = False
        st.session_state.eliza_bot = None
        st.session_state.messages = []
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Enter your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = st.session_state.eliza_bot.respond(prompt)
            
            if response is None:
                response = random.choice(st.session_state.eliza_bot.finals)
                st.info("Chat ended.")
            
            message_placeholder = st.empty()
            full_response = ""

            for chunk in response:
                full_response += chunk
                time.sleep(0.02)
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

initialize_session_state()

if st.session_state.chat_started and st.session_state.eliza_bot:
    render_chat_screen()
else:
    render_config_screen()
