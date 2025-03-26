import streamlit as st
import requests
import json
import pandas as pd


# API Endpoints
BASE_URL = "http://127.0.0.1:5000"
RECONCILE_API = f"{BASE_URL}/reconcile"
CHAT_OPTIONS_API = f"{BASE_URL}/chat/options"
CHAT_SELECT_API = f"{BASE_URL}/chat/select"
CHAT_EXECUTE_API = f"{BASE_URL}/chat/execute"
LOAD_CONFIG_API = f"{BASE_URL}/load/config"
TRAIN_MODEL_API = f"{BASE_URL}/train/model"

# Streamlit Page Config
st.set_page_config(page_title="Reconciliation Chatbot", layout="wide")
st.title("Reconciliation Chatbot 🤖")
st.markdown("Type **Load Config** to load your configuration file.")
st.markdown("Type **Reconcile data** to load your input file.")
st.markdown("Type **Train Model** to load your historic data file.")

# Initialize session states
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "show_upload_fields" not in st.session_state:
    st.session_state.show_upload_fields = False
if "show_reconcile_fields" not in st.session_state:
    st.session_state.show_reconcile_fields = False
if "show_config_upload" not in st.session_state:
    st.session_state.show_config_upload = False
if "next_step_options" not in st.session_state:
    st.session_state.next_step_options = {}
if "selected_option" not in st.session_state:
    st.session_state.selected_option = None
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""
if "input_fields" not in st.session_state:
    st.session_state.input_fields = {}
if "api_called" not in st.session_state:
    st.session_state.api_called = False  # Track API call status



def display_chat():
    """Display chat messages."""
    for entry in st.session_state.chat_history:
        with st.chat_message(entry["role"]):
            st.markdown(f"**{entry['role'].capitalize()}**: {entry['content']}")

     # Display next-step options as a dropdown and button
    if st.session_state.next_step_options:
        st.subheader("Next Steps")
        selected_option_value = st.selectbox("Choose an action:", list(st.session_state.next_step_options.values()))
        selected_option_key = [key for key, value in st.session_state.next_step_options.items() if value == selected_option_value][0]

        if st.button("Proceed"):
            with st.spinner("Processing your selection..."):
                st.session_state.selected_option = selected_option_value
                try:
                    response = requests.post(CHAT_SELECT_API, json={"option": selected_option_key})
                    response.raise_for_status()
                    result = response.json()
                    st.session_state.generated_code = result.get("generated_code", "")
                    st.session_state.input_fields = result.get("input_fields", [])
                    st.session_state.chat_history.append({"role": "Reconciliation Agent", "content": f"Selected: {selected_option_value}\n\n```json\n"})
                    st.session_state.next_step_options = {}
                except requests.exceptions.RequestException:
                    st.session_state.chat_history.append({"role": "Reconciliation Agent", "content": "Backend service error."})
                st.rerun()
    if st.session_state.input_fields:
        st.subheader("Provide Required Inputs")
        user_inputs = {}
        for field in st.session_state.input_fields:
            user_inputs[field] = st.text_input(field)

        if st.button("Submit"):
            with st.spinner("Executing the selected option..."):
                try:
                    response = requests.post(CHAT_EXECUTE_API, json={
                        "generated_code": st.session_state.generated_code,
                        "user_inputs": user_inputs,
                    })
                    response.raise_for_status()
                    result = response.json()
                    st.session_state.chat_history.append({"role": "Reconciliation Agent", "content": f"✅ Task '{st.session_state.selected_option}' was successfull!"})
                    st.session_state.input_fields = {}
                    st.session_state.next_step_options = {}
                    st.toast(f"✅ Task '{st.session_state.selected_option}' was executed successfully!")
                    st.success("Execution successful!")
                except requests.exceptions.RequestException:
                    st.error("Error executing the selected option.")
                st.rerun()

    # Config Upload Section
    if st.session_state.show_config_upload:
        st.subheader("Upload Configuration File")
        config_file = st.file_uploader("Upload JSON Config File", type=["json"], key="config_file")
        if st.button("Load Config"):
            if config_file:
                files = {"config_file": (config_file.name, config_file, "application/json")}
                with st.spinner("Loading configuration... Please wait."):
                    try:
                        response = requests.post(LOAD_CONFIG_API, files=files)
                        response.raise_for_status()
                        result = response.json()

                        # Append response to chat history
                        formatted_result = json.dumps(result, indent=2)
                        st.session_state.chat_history.append({
                            "role": "Reconciliation Agent",
                            "content": f"Config Load Response:\n\n```json\n{formatted_result}\n```"
                        })

                        st.success("Configuration loaded successfully! ✅")
                        st.session_state.chat_history.append(
                            {"role": "Reconciliation Agent", "content": "Configuration loaded successfully! ✅"})
                        st.session_state.show_config_upload = False
                        st.rerun()
                    except requests.exceptions.RequestException:
                        st.error("Backend service error. Please try again.")
                        st.session_state.chat_history.append({"role": "Reconciliation Agent", "content": "Backend service error."})
            else:
                st.warning("Please upload a config file.")

    # Training Model Upload Section
    if st.session_state.show_upload_fields:
        st.subheader("Upload Training Files")
        train_data_file = st.file_uploader("Upload training dataset", type=["csv", "xlsx"], key="train_data_file")
        if st.button("Train Model"):
            if train_data_file:
                files = {"historical_file": (train_data_file.name, train_data_file,
                                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                with st.spinner("Training model... Please wait."):
                    try:
                        response = requests.post(TRAIN_MODEL_API, files=files)
                        response.raise_for_status()
                        result = response.json()

                        # Append response to chat history
                        formatted_result = json.dumps(result, indent=2)
                        st.session_state.chat_history.append({
                            "role": "Reconciliation Agent",
                            "content": f"Model Training Response:\n\n```json\n{formatted_result}\n```"
                        })

                        st.success("Model has been updated with the history file... ✅")
                        st.session_state.chat_history.append(
                            {"role": "Reconciliation Agent", "content": "Model has been updated with the history file... ✅"})
                        st.session_state.show_upload_fields = False
                        st.rerun()
                    except requests.exceptions.RequestException:
                        st.error("Backend service error. Please try again.")
                        st.session_state.chat_history.append({"role": "Reconciliation Agent", "content": "Backend service error."})
            else:
                st.warning("Please upload a training dataset.")

    # Reconciliation Upload Section
    if st.session_state.show_reconcile_fields:
        st.subheader("Upload Reconciliation Files")
        current_data_file = st.file_uploader("Current Data File", type=["csv", "xlsx"], key="current_data_file")

        if st.button("Start Reconciliation") and not st.session_state.api_called:
            st.session_state.api_called = True  # Mark API as called
            st.rerun()  # Refresh UI to prevent duplicate calls

    if st.session_state.api_called:
        st.session_state.api_called = False  # Reset API call flag
        if current_data_file:
            files = {
                "file": (current_data_file.name, current_data_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            }
            with st.spinner("Processing reconciliation..."):
                try:
                    response = requests.post(RECONCILE_API, files=files)
                    response.raise_for_status()
                    result = response.json()
                    message = f"Reconciliation complete.\n\n```json\n{result}\n```"
                    st.session_state.chat_history.append({"role": "system", "content": message})
                    st.session_state.show_reconcile_fields = False
                    if isinstance(result, dict) and "anomalous_records" in result:
                        df = pd.DataFrame(result["anomalous_records"])  # Convert anomalous records to DataFrame
                        table_str = df.to_markdown(index=False)  # Convert DataFrame to markdown table
                        message = f"### Reconciliation Results (Anomalous Count: {result.get('anomalous_count', 0)})\n\n```\n{table_str}\n```"
                    else:
                        message = "Reconciliation complete, but no anomalous records found."

                # Append message to chat history
                    st.session_state.chat_history.append({"role": "system", "content": message})
                    
                    # Show next step options if anomalies exist
                    if result.get("anomalous_count", 0) > 0:
                        options_response = requests.get(CHAT_OPTIONS_API)
                        st.session_state.next_step_options = options_response.json()
                    
                    st.rerun()
                except requests.exceptions.RequestException:
                    st.session_state.chat_history.append({"role": "system", "content": "Backend service error."})
        else:
            st.warning("Please upload all required files.")

# Handle chat interaction
def handle_chat(user_message):
    """Handle user input in the chat."""
    st.session_state.chat_history.append({"role": "Operator", "content": f"{user_message}"})

    if "train" in user_message.lower():
        st.session_state.chat_history.append({"role": "Reconciliation Agent", "content": "Training started. Upload your dataset below."})
        st.session_state.show_upload_fields = True
        st.rerun()

    elif "load config" in user_message.lower():
        st.session_state.chat_history.append({"role": "Reconciliation Agent", "content": "Please upload your configuration file below."})
        st.session_state.show_config_upload = True
        st.rerun()

    elif "reconcile" in user_message.lower():
        st.session_state.chat_history.append({"role": "Reconciliation Agent", "content": "Please upload files for reconciliation below."})
        st.session_state.show_reconcile_fields = True
        st.rerun()

    else:
        st.session_state.chat_history.append({"role": "Reconciliation Agent", "content": "I didn't understand. Try  'Load Config', 'Train Model',  or 'Reconcile Data'."})


# Display chat messages
if st.button("Clear Chat"):
    st.session_state.chat_history = []
    st.session_state.show_config_upload = False
    st.session_state.show_upload_fields = False
    st.rerun()

# Display chat history
display_chat()


# Get user input
user_message = st.chat_input("Type your message...")
if user_message:
    handle_chat(user_message)
    display_chat()
