🎓 UoM Tutor Agent & Quiz Generator
An AI-powered educational assistant designed for the "Software Quality" course at the University of Macedonia (UoM/ΠΑΜΑΚ).

This application provides a personalized learning interface where students can chat with an AI Tutor about course materials and generate dynamic quizzes based on their learning session history.

🚀 Key Features
User Authentication: Secure login system verifying credentials against a local registry.

AI Tutor Chat: Interactive chat interface using Google Gemini and LangChain.

Uses RAG (Retrieval-Augmented Generation) to answer questions based on course documents.

Maintains conversation history.

Dynamic Quiz Generator: Automatically generates multiple-choice questions (in Greek) based on the summary of the user's chat session.

Interactive GUI: Built with FreeSimpleGUI for a clean, user-friendly desktop experience.

Progress Tracking: Uses a local SQLite database (classroom.db) to store student profiles and session summaries.

Cloud/Local Sync: Capabilities to upload session summaries for future reference.

🛠️ Tech Stack
Language: Python 3.x

GUI: FreeSimpleGUI

AI & LLM: LangChain, Google Gemini (via langchain-google-genai)

Data Handling: Pandas, SQLite3

Environment: Python-dotenv

Packaging: PyInstaller (Spec file included for macOS/Windows builds)

📂 Project Structure
Plaintext

├── interface.py       # Main entry point. Handles the GUI and User Login.
├── questions.py       # AI Logic for generating JSON-formatted quizzes.
├── tutor_tools.py     # LangChain tools (Database upload, RAG retrieval).
├── users.csv          # Local user registry (Username/Password/ID).
├── UoM_Tutor.spec     # PyInstaller configuration for building the executable.
├── cloud.py           # Database helper scripts for initialization.
└── .env               # API Keys (Not included in repo).
⚙️ Installation & Setup
1. Clone the Repository
Bash

git clone https://github.com/your-username/uom-tutor-agent.git
cd uom-tutor-agent
2. Install Dependencies
Ensure you have Python installed. It is recommended to use a virtual environment.

Bash

# Install required libraries (Example)
pip install FreeSimpleGUI pandas python-dotenv langchain langchain-google-genai sqlite3
3. Configure Environment Variables
Create a .env file in the root directory and add your Google Gemini API key:

Ini, TOML

GEMINI_API_KEY=your_google_api_key_here
4. Database Setup
The application automatically handles the creation of the SQLite database (classroom.db) in the user's home directory. However, ensure users.csv is present in the root folder for authentication.

🖥️ Usage
Running the Application
To start the interface, run the following command:

Bash

python interface.py
User Login
Use the credentials found in users.csv to log in.

Example User: maria

Password: securepwd

Navigation
🏠 Home: Welcome screen.

💬 Tutor: Chat with the AI regarding "Software Quality". When finished, click "Τέλος Συνεδρίας" (End Session) to save your summary.

❓ Quiz: After a session is saved, generate a quiz to test your knowledge.

ℹ️ About: Information about the tool.

📦 Building an Executable
The repository includes a UoM_Tutor.spec file. You can bundle the application into a standalone executable (.exe or .app) using PyInstaller:

Bash

pyinstaller UoM_Tutor.spec
The output will be located in the dist/ folder.

⚠️ Important Notes
Language: The application interface and AI responses are primarily in Greek.

Data Privacy: The classroom.db database is stored locally in the user's home directory (e.g., C:\Users\Name\classroom.db or /Users/Name/classroom.db).

Missing Files: Ensure tutor.py (referenced in imports) is present in your local directory for the Chat Agent to function correctly.

📜 License
This project is created for educational purposes at the University of Macedonia.

Author: [Your Name] Contact: [Your Email/Link]