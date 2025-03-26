import concurrent.futures
import json
import os
import re
import textwrap

import joblib
import ollama
import pandas as pd
from flask import Flask, request, jsonify
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine

# Initialize Flask Backend
app = Flask(__name__)
MODEL_PATH = "anomaly_model.pkl"
DB_URL = "postgresql://myuser:mypassword@localhost:5432/reconciliation_db"
engine = create_engine(DB_URL)
config={}

def generate_comments(comment_prompt, derived_values, historical_values):
    prompts = [
        comment_prompt.format(derived_value=dv, historical_value=hv)
        for dv, hv in zip(derived_values, historical_values)
    ]

    def fetch_comment(prompt):
        response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"].strip()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        responses = list(executor.map(fetch_comment, prompts))

    return responses


def train_anomaly_model(historical_dataframe, feature_columns):
    if historical_dataframe.empty:
        return None

    scaler = StandardScaler()
    features = historical_dataframe[feature_columns].to_numpy()
    scaled_features = scaler.fit_transform(features)
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(scaled_features)
    joblib.dump((model, scaler), MODEL_PATH)
    return model


def predict_anomalies(dataframe, feature_columns):
    if not os.path.exists(MODEL_PATH):
        return ["Unknown"] * len(dataframe)

    model, scaler = joblib.load(MODEL_PATH)
    features = dataframe[feature_columns].to_numpy()
    scaled_features = scaler.transform(features)

    anomaly_scores = model.predict(scaled_features)
    return ["No" if score == 1 else "Yes" for score in anomaly_scores]

def get_anamoly_columns(dataframe):
  
    key_columns = config.get("key_columns", [])
    criteria_columns = config.get("criteria_columns", [])
    derived_column_name = config.get("derived_column", "Balance Difference")
    comment_column_name = config.get("comment_column", "Comments")
    comment_prompt = config.get("comment_prompt", "")
    compare_current_criteria_column = config.get("compare_current_criteria_column", True)

    dataframe.columns = dataframe.columns.str.strip()
    criteria_columns = [col for col in criteria_columns if col in dataframe.columns]

    if not criteria_columns:
        raise ValueError("No valid criteria columns found in DataFrame.")

    for col in criteria_columns:
        dataframe[col] = pd.to_numeric(dataframe[col], errors="coerce")

    difference_columns = []

    if compare_current_criteria_column:
        dataframe[derived_column_name] = dataframe[criteria_columns[0]] - dataframe[criteria_columns[1]]
        difference_columns.append(derived_column_name)
    else:
        db_columns = config.get("db_columns", "").split(",")

        if len(db_columns) < 2:
            raise ValueError("Please provide at least two database column names in 'db_columns' (comma-separated).")

        db_column_1, db_column_2 = db_columns[:2]

        for col in criteria_columns:
            col_1 = f"{db_column_1} {col}".strip()
            col_2 = f"{db_column_2} {col}".strip()

            if col_1 in dataframe.columns and col_2 in dataframe.columns:
                diff_col_name = f"Difference {col}"
                dataframe[diff_col_name] = dataframe[col_1] - dataframe[col_2]
                difference_columns.append(diff_col_name)

    # Set "Match Status" based on the first nonzero difference column
    def determine_match_status(row):
        for col in difference_columns:
            if row[col] != 0:  # First nonzero difference determines the status
                return f"{col.replace('Difference ', '')} Break"
        return "Match"

    dataframe["Match Status"] = dataframe.apply(determine_match_status, axis=1)
    return difference_columns if not compare_current_criteria_column else criteria_columns

def process_reconciliation(dataframe):
    key_columns = config.get("key_columns", [])
    criteria_columns = config.get("criteria_columns", [])
    derived_column_name = config.get("derived_column", "Balance Difference")
    comment_column_name = config.get("comment_column", "Comments")
    comment_prompt = config.get("comment_prompt", "")
    compare_current_criteria_column = config.get("compare_current_criteria_column", True)

    dataframe.columns = dataframe.columns.str.strip()
    criteria_columns = [col for col in criteria_columns if col in dataframe.columns]

    if not criteria_columns:
        raise ValueError("No valid criteria columns found in DataFrame.")

    for col in criteria_columns:
        dataframe[col] = pd.to_numeric(dataframe[col], errors="coerce")

    difference_columns = []

    if compare_current_criteria_column:
        dataframe[derived_column_name] = dataframe[criteria_columns[0]] - dataframe[criteria_columns[1]]
        difference_columns.append(derived_column_name)
    else:
        db_columns = config.get("db_columns", "").split(",")

        if len(db_columns) < 2:
            raise ValueError("Please provide at least two database column names in 'db_columns' (comma-separated).")

        db_column_1, db_column_2 = db_columns[:2]

        for col in criteria_columns:
            col_1 = f"{db_column_1} {col}".strip()
            col_2 = f"{db_column_2} {col}".strip()

            if col_1 in dataframe.columns and col_2 in dataframe.columns:
                diff_col_name = f"Difference {col}"
                dataframe[diff_col_name] = dataframe[col_1] - dataframe[col_2]
                difference_columns.append(diff_col_name)

    # Set "Match Status" based on the first nonzero difference column
    def determine_match_status(row):
        for col in difference_columns:
            if row[col] != 0:  # First nonzero difference determines the status
                return f"{col.replace('Difference ', '')} Break"
        return "Match"

    dataframe["Match Status"] = dataframe.apply(determine_match_status, axis=1)

    # Use computed difference columns for anomaly detection
    anomaly_columns = difference_columns if not compare_current_criteria_column else criteria_columns

    # Load historical data
    historical_dataframe = pd.DataFrame()
    

    dataframe["Anomaly"] = predict_anomalies(dataframe, anomaly_columns)

    # Generate comments only if there's a derived column
    if compare_current_criteria_column:
        anomaly_mask = dataframe["Anomaly"] == "Yes"
    
        if anomaly_mask.any():  
            historical_avg = [0] * len(dataframe)  # Replace with actual historical values if available
            dataframe[comment_column_name] =generate_comments(
                comment_prompt, dataframe[derived_column_name].tolist(), historical_avg
            )

    non_anomalous_records = dataframe[dataframe["Anomaly"] == "No"]
    #non_anomalous_records.to_sql("matched_records", engine, if_exists="append", index=False)
    
    anomalous_records = dataframe[dataframe["Anomaly"] == "Yes"]
    return len(dataframe), len(anomalous_records), anomalous_records


@app.route("/reconcile", methods=["POST"])
def reconcile():
    try:
        file = request.files.get("file")

        if not file:
            return jsonify({"error": "Missing required files."})

        dataframe = pd.read_excel(file)
        

        processed_count, anomalous_count, anomalous_records = process_reconciliation(dataframe)

        return jsonify({
            "message": "Processing complete.",
            "processed_count": processed_count,
            "anomalous_count": anomalous_count,
            "anomalous_records": anomalous_records.to_dict(orient="records")
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/load/config', methods=['POST'])
def load_configfile():
    global config
    config_file = request.files.get("config_file")
    config = json.load(config_file)
    print(config)
    return jsonify({
            "message": "Config file loaded successfully into the system."
        })
        
@app.route('/train/model', methods=['POST'])
def train_model():
    historical_file = request.files.get("historical_file")
    if historical_file:
        historical_dataframe = pd.read_excel(historical_file)
    else:
        try:
            with engine.connect() as conn:
                query = f"SELECT {', '.join([f'\"{col}\"' for col in anomaly_columns])} FROM matched_records LIMIT 1000"
                historical_dataframe = pd.read_sql_query(query, conn)
        except Exception as e:
            print(f"No historical data found: {e}")

    if not historical_dataframe.empty:
        anomaly_columns=get_anamoly_columns(historical_dataframe) 
        train_anomaly_model(historical_dataframe, anomaly_columns)
    return jsonify({
            "message": "Model has been updated with the current history file"
        })

@app.route('/chat/options', methods=['GET'])
def get_options():
    NEXT_STEP_OPTIONS = config.get("next_step_options",{
                "1": "Send an Email",
                "2": "Create a Jira Ticket",
                "3": "Generate a Report",
                "4": "Update Source"
            })
    return jsonify(NEXT_STEP_OPTIONS)

@app.route('/chat/select', methods=['POST'])
def select_option():
    data = request.json
    option = data.get("option", "")
    NEXT_STEP_OPTIONS = config.get("next_step_options",{
                "1": "Send an Email",
                "2": "Create a Jira Ticket",
                "3": "Generate a Report"
            })

    if option not in NEXT_STEP_OPTIONS:
        return jsonify({"error": "Invalid option"}), 400

    prompt = f"""
            You are a highly skilled Python developer. Your task is to generate a **fully functional Python function** that {NEXT_STEP_OPTIONS[option].lower()}.

            ### Strict Requirements:
            - The function **must** collect user input dynamically using `input()`.
            - **Output must be Python code only** – **DO NOT** include explanations, comments, or placeholder text.
            - The function **must be executable without modification**.
            - **Ensure the code is properly formatted and indented.**
            - **DO NOT** include example inputs/outputs or explanations.
            - **DO NOT** include import statments the function alone is enough.
            """



    generated_code = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
    generated_code= generated_code["message"]["content"].strip()
    print("Generated Code:\n", generated_code) 
    input_fields = extract_input_fields(generated_code)
    print("input fields",input_fields)
    return jsonify({
        "message": f"{NEXT_STEP_OPTIONS[option]} selected.",
        "generated_code": generated_code,
        "input_fields": input_fields
    })

def extract_input_fields(code):
    """Extracts input fields from the generated code using regex."""
    input_fields = re.findall(r'input\s*\(\s*["\'](.*?)["\']\s*\)', code)
    return input_fields

@app.route('/chat/execute', methods=['POST'])
def execute_generated_code():
    data = request.json
    generated_code = data.get("generated_code", "")
    user_inputs = data.get("user_inputs", {})

    if not generated_code or not user_inputs:
        return jsonify({"error": "Generated code and user inputs are required"}), 400

    # Normalize indentation
    cleaned_code = textwrap.dedent(generated_code).strip()

    # Replace input() calls with user inputs
    for field, value in user_inputs.items():
        cleaned_code = cleaned_code.replace(f"input('{field}')", f"'{value}'")

    try:
        #exec(cleaned_code, globals())
        return jsonify({"message": "Generated code executed successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
		
if __name__ == "__main__":
    app.run(debug=True)