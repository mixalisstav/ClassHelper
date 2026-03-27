<div align="center">

## 🎓 UoM Tutor Agent & Quiz Generator

**An AI-powered study buddy** for the *Software Quality* course at the University of Macedonia (UoM/ΠΑΜΑΚ).  
Chat with an AI Tutor, learn from course docs (RAG), then generate quizzes from your session history. ✨

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Desktop App](https://img.shields.io/badge/Desktop%20App-FreeSimpleGUI-6C5CE7)
![LangChain](https://img.shields.io/badge/LangChain-powered-1C3C3C)
![Gemini](https://img.shields.io/badge/Google%20Gemini-LLM-4285F4?logo=google&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-local%20db-003B57?logo=sqlite&logoColor=white)

</div>

---

## ✨ What it does

- **🔐 User login**: Verifies credentials from a local registry (`users.csv`).
- **💬 AI Tutor chat**: Conversational tutor powered by **LangChain + Google Gemini**.
  - **📚 RAG**: Answers questions grounded in course documents.
  - **🧠 Memory**: Keeps conversation history during your session.
- **❓ Quiz generator (Greek)**: Creates multiple-choice questions from your saved session summary.
- **📈 Progress tracking**: Saves student profiles + session summaries in a local SQLite DB (`classroom.db`).
- **☁️ Sync-ready**: Includes utilities for uploading session summaries for later reference.

---

## 🧰 Tech stack

- **Language**: Python 3.x
- **GUI**: FreeSimpleGUI
- **LLM**: LangChain + Google Gemini (`langchain-google-genai`)
- **Vector DB / RAG**: ChromaDB + Unstructured
- **Data**: pandas + SQLite (built-in)
- **Packaging**: PyInstaller

---

## 🗂️ Project layout (high level)

```text
.
├── interface.py        # GUI + user login + navigation
├── tutor.py            # Tutor/chat logic
├── questions.py        # Quiz generation logic (JSON-style quiz output)
├── tutor_tools.py      # LangChain tools (RAG retrieval, uploads, etc.)
├── cloud.py            # DB / initialization helpers
├── users.csv           # Local user registry (username/password/id)
├── requirements.txt    # Python dependencies
└── .env                # API keys (local only; do not commit)
```

---

## ⚙️ Setup (local)

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Add your API key

Create a `.env` file in the project root:

```bash
GEMINI_API_KEY=your_google_api_key_here
```

### 3) Run the app

```bash
python interface.py
```

---

## 🧭 How to use (quick tour)

- **🏠 Home**: Welcome screen
- **💬 Tutor**: Chat about *Software Quality*. When you’re done, click **"Τέλος Συνεδρίας"** (End Session) to save a summary.
- **❓ Quiz**: After you save a session, generate a quiz to test your knowledge.
- **ℹ️ About**: Project info

---

## 📦 Build an executable (optional)

If you’re packaging the app, use PyInstaller:

```bash
pyinstaller UoM_Tutor.spec
```

The output will appear in `dist/`.

---

## 🔎 Notes & gotchas

- **🇬🇷 Language**: UI + responses are primarily in Greek.
- **🗄️ Data privacy**: `classroom.db` is stored locally in the user’s home directory (e.g. `~/classroom.db` on macOS/Linux, or `C:\Users\Name\classroom.db` on Windows).
- **🔑 Secrets**: Keep `.env` private—never commit API keys.

---

## 📜 License

Created for practice at the University of Macedonia.

## 🙌 Author

- **Name**: Michael Tsampikos Stavrianakis
- **Contact**: mstavrianakes@gmail.com