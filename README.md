# 🚀 Project Name

## 📌 Table of Contents
- [Introduction](#introduction)
- [Demo](#demo)
- [Inspiration](#inspiration)
- [What It Does](#what-it-does)
- [How We Built It](#how-we-built-it)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Team](#team)

---

## 🎯 Introduction
The Dynamic Financial Data Reconciliation System is an advanced, all-in-one solution designed to process financial records, identify anomalies, and empower users with AI-driven insights via an interactive chatbot. Leveraging a microservices architecture, the system incorporates a Flask backend for optimized data processing and a user-friendly Streamlit frontend for seamless interaction.
 One of its standout features is its flexibility—by utilizing a dynamic configuration file (config.json), the system can effortlessly handle any dataset without the need for hardcoded column names. This adaptability ensures scalability, customization, and broad compatibility with a wide range of financial reconciliation scenarios.
## 🎥 Demo
🔗 [Live Demo](#) Demo has been placed in the demo folder

## ⚙️ What It Does
User-friendly Conversational AI (chatbot integration) for reconciling financial records.
Provides AI-driven chatbot assistance for next-step actions.
Displays processed reconciliation results, including anomalies.
Recommends next steps/actions.
Agent-AI can generate code and run code to take specific action as per configuration.
Processes financial data and performs reconciliation.
Hosts APIs for anomaly detection, matching records, and generating insights.
Integrates with the OLLAMA  model for automated response generation.
Processes uploaded files.
Reads the configuration file dynamically.
Applies reconciliation logic.
Uses ML to detect anomalies and AI to generate comments.


## 🛠️ How We Built It
1. Frontend (Streamlit UI)
2. Backend (Flask API Server)
3. Database (postgres) - Create sql attached
4. Machine Learning (Anomaly Detection)
5. AI-Powered Chatbot

## 🏃 How to Run
1. Clone the repository  
   ```sh
   git clone https://github.com/your-repo.git
   ```
2. Install dependencies  
   ``` pip install -r requirements.txt (for Python)
   ```
   Requirements file has been placed in the src folder
3. Run the project  
   ``` python frontend.py
	   python backend.py
   ```

## 🏗️ Tech Stack
- 🔹 Frontend: Streamlit Python Api
- 🔹 Backend: Flask Python Api
- 🔹 Database: PostgreSQL
- 🔹 Other: OLLAMA Model

## 👥 Team
- **Mariappan**
- **Rajesh** 
- **Swarna**
- **Palraj**
- **Prabhu**