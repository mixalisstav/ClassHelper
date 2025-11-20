import os
import sqlite3 as sql
import json
from dotenv import load_dotenv

# Φορτώνει το API KEY
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

from tutor import get_user_credentials # Υποθέτουμε ότι υπάρχει αυτό το αρχείο

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage # Χρειάζεται για το chat_history

# 1. ΟΡΙΣΜΟΣ ΤΟΥ JSON ΣΧΗΜΑΤΟΣ ΓΙΑ ΤΟ QUIZ
# Αυτό είναι απαραίτητο για να διαβάσει η εφαρμογή σας τις ερωτήσεις σωστά.
QUIZ_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "question_text": {"type": "string", "description": "Το κείμενο της ερώτησης πολλαπλής επιλογής."},
            "options": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ακριβώς τέσσερις πιθανές απαντήσεις (επιλογές) για την ερώτηση."
            },
            "correct_answer": {"type": "string", "description": "Η σωστή απάντηση, η οποία πρέπει να ταιριάζει με μία από τις επιλογές."}
        },
        "required": ["question_text", "options", "correct_answer"]
    }
}


llm = ChatGoogleGenerativeAI(
    api_key=API_KEY,
    model="gemini-2.5-flash",
    temperature=0.2,
)

# 2. ΤΟ TEMPLATE ΤΟΥ ΣΥΣΤΗΜΑΤΟΣ (System Prompt)
# ΔΙΟΡΘΩΣΗ: Οι αγκύλες του JSON Schema Example έχουν γίνει διπλές (π.χ. { -> {{ ) για να αποφευχθεί
# το σφάλμα Key Error του LangChain.
TEMPLATE = """
You are an Automated Quiz Generator and Assessment Specialist.
Your sole purpose is to generate highly relevant, single-answer multiple-choice questions (MCQs) based on the provided session summary.

***INPUT DATA & CONTEXT***

1.  **SUMMARY:** The main topic and learning points discussed in the tutor session.
2.  **LANGUAGE:** The language used for the quiz questions MUST be Greek (Ελληνικά).
3.  **DIFFICULTY:** Assume a medium difficulty level appropriate for a University of Macedonia student in Software Quality.

***OUTPUT REQUIREMENT (MANDATORY)***
You will generate as many questions as possible (minimum 5, maximum 10) based on the summary provided.
Your entire output MUST be a valid JSON array matching the provided schema. Do NOT include any introductory text, explanatory notes, or markdown outside of the JSON block.

Schema Example for ONE Question (Output must strictly adhere to this format):
[[
  {{
    "question_text": "Ποιο είναι το κύριο όφελος της δοκιμής τύπου white-box;",
    "options": ["Επαλήθευση απαιτήσεων", "Βελτιστοποίηση κώδικα", "Μέτρηση ικανοποίησης χρήστη", "Αξιολόγηση διεπαφής χρήστη"],
    "correct_answer": "Βελτιστοποίηση κώδικα"
  }}
]]
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", TEMPLATE),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 3. ΟΡΙΣΜΟΣ AGENT
tools=[]

agent = create_openai_tools_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
)
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
)   

def main(name, id):
    # Σύνδεση με τη βάση δεδομένων
    conn = sql.connect('classroom.db')
    c = conn.cursor()
    
    # 4. ΔΙΟΡΘΩΣΗ ΑΝΑΚΤΗΣΗΣ ΣΥΝΟΨΗΣ
    # Η σωστή ανάκτηση πρέπει να διαλέξει το σωστό πεδίο από το tuple.
    c.execute('''SELECT questions FROM students WHERE name=? AND id=?''', (name, id))
    result = c.fetchone()
    c.close()
    conn.close()
    
    if result is None or not result[0]:
        print("Δεν βρέθηκε σύνοψη συνεδρίας για τον συγκεκριμένο χρήστη. Αδύνατη η δημιουργία κουίζ.")
        return 0
    
    # Η σύνοψη βρίσκεται στο πρώτο στοιχείο του tuple, και είναι ήδη string (text/json).
    summary_data_string = result[0]
    
    # Το αρχικό summary μπορεί να είναι ένα JSON string (π.χ. '{}') ή ένα κείμενο.
    # Εάν είναι JSON από παλιά δεδομένα, παίρνουμε το κείμενο. Εδώ υποθέτουμε ότι είναι η σύνοψη ως κείμενο.
    print("Session summary retrieved (Raw Data):", summary_data_string)
    
    # 5. ΚΑΘΟΡΙΣΜΟΣ GENERATION CONFIG ΓΙΑ JSON
    # Αυτό είναι το κρίσιμο βήμα για να αναγκάσει το μοντέλο να παράγει JSON.
    generation_config = {
        "responseMimeType": "application/json",
        "responseSchema": QUIZ_SCHEMA
    }
    
    # Το agent_executor.invoke δεν δέχεται 'generation_config' απευθείας.
    # Εδώ, το περνάμε ως μέρος της κλήσης LLM Agent (πρέπει να γίνει στο AgentExecutor
    # αν το μοντέλο το υποστηρίζει, ή να γίνει άμεση κλήση του LLM με το config).
    # Για το LangChain, πρέπει να περάσουμε το config μέσω του LLM.

    # Λόγω του περιορισμού του LangChain AgentExecutor να μην δέχεται εύκολα generation_config, 
    # θα χρησιμοποιήσουμε ένα πιο ρητό prompt και το Gemini API θα αναγκαστεί να παράξει JSON 
    # λόγω της ισχυρής System Instruction. Για μια πλήρη λύση, θα κάναμε άμεση κλήση του LLM
    # αντί για τον AgentExecutor. Ωστόσο, για να παραμείνουμε στο LangChain Agent, 
    # θα βάλουμε τη δομή JSON στο prompt ως μια ισχυρή απαίτηση.

    # 6. ΔΙΟΡΘΩΣΗ INVOKE ARGUMENTS
    response = agent_executor.invoke(
        input={
            # Η σύνοψη περνιέται ως μέρος του ερωτήματος (question)
            "question": f"Generate multiple-choice questions based on the following session summary: {summary_data_string}",
            # Το chat_history πρέπει να είναι λίστα από μηνύματα (HumanMessage, AIMessage), όχι string.
            "chat_history": [HumanMessage(content=f"Ονομα: {name}, Αριθμός Μητρώου: {id}")],
        },
        # Προσθήκη generation_config στην κλήση του LLM (για το Gemini AgentExecutor)
        # Σημείωση: Αν και το AgentExecutor δεν το χειρίζεται πάντα σωστά, το συμπεριλαμβάνουμε
        # ως επιχείρημα για να επηρεάσει το μοντέλο.
        config={'configurable': {'llm_config': generation_config}}
    )
    
    # Επειδή ζητήσαμε JSON, η έξοδος θα πρέπει να είναι JSON string.
    try:
        json_output = response['output'].strip().replace("```json", "").replace("```", "")
        questions = json.loads(json_output)
        print("\n--- SUCCESSFULLY PARSED QUIZ QUESTIONS (ΕΛΛΗΝΙΚΑ) ---")
        print(json.dumps(questions, indent=2, ensure_ascii=False))
        return questions
    except json.JSONDecodeError as e:
        print("\n--- ERROR PARSING JSON OUTPUT ---")
        print(f"Failed to decode JSON from model output. Error: {e}")
        print("Raw model output:", response['output'])
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    
    

if __name__ == "__main__":
    # Υποθέτουμε ότι η συνάρτηση get_user_credentials λειτουργεί
    trig, name, id = get_user_credentials()
    
    if trig: 
        print(f"Επιτυχής ταυτοποίηση για τον χρήστη {name} (ID: {id}).")
        main(name=name, id=id)
    else:
        print("Η ταυτοποίηση απέτυχε. Το πρόγραμμα τερματίζεται.")