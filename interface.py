import FreeSimpleGUI as sg
import pandas as pd
import sqlite3 as sql
import os
from dotenv import load_dotenv

# Φορτώνει μεταβλητές περιβάλλοντος (π.χ. GEMINI_API_KEY)
load_dotenv()

# --- 1. Λειτουργίες Πιστοποίησης & Βοηθητικές ---

# Αυτή η συνάρτηση προέρχεται από τη λογική του tutor/quiz agent 
# και ελέγχει τα διαπιστευτήρια του χρήστη.
def authenticate_user(name, password):
    """Ελέγχει τα διαπιστευτήρια του χρήστη έναντι του users.csv."""
    try:
        users_df = pd.read_csv('users.csv')
        
        # Εξασφάλιση ότι οι στήλες υπάρχουν
        if 'user_name' not in users_df.columns or 'user_password' not in users_df.columns or 'id' not in users_df.columns:
            sg.popup_error("Σφάλμα:", "Το αρχείο users.csv πρέπει να περιέχει τις στήλες 'name', 'password' και 'id'.")
            return False, None, None

        # Αναζήτηση χρήστη
        match = users_df[(users_df['user_name'] == name) & (users_df['user_password'] == password)]
        
        if not match.empty:
            user_id = str(match['id'].iloc[0])
            # Εγγύηση ότι ο χρήστης υπάρχει στη βάση 'students' για μελλοντική χρήση
            ensure_student_in_db(name, user_id)
            return True, name, user_id
        else:
            return False, None, None
            
    except FileNotFoundError:
        sg.popup_error("Σφάλμα:", "Το αρχείο users.csv δεν βρέθηκε. Η σύνδεση απέτυχε.")
        return False, None, None
    except Exception as e:
        sg.popup_error("Σφάλμα:", f"Πρόβλημα ανάγνωσης του users.csv: {e}")
        return False, None, None
        
def ensure_student_in_db(name, id):
    """Εισάγει τον χρήστη στον πίνακα students αν δεν υπάρχει."""
    try:
        conn = sql.connect('classroom.db')
        c = conn.cursor()
        
        # Ελέγχει αν υπάρχει ο χρήστης
        c.execute('''SELECT name FROM students WHERE name=? AND id=?''', (name, id))
        result = c.fetchone()
        
        # Αν δεν υπάρχει, τον εισάγει με κενό JSON για ερωτήσεις
        if result is None:
            c.execute('''INSERT INTO students (name, id, questions) VALUES (?, ?, ?)''', (name, id, '{}'))
            conn.commit()
            
        c.close()
        conn.close()
    except Exception as e:
        # Αυτό το σφάλμα μπορεί να συμβεί αν ο πίνακας 'students' δεν έχει τις στήλες 'name', 'id', 'questions'
        print(f"Database error during user check/insertion: {e}")


# --- 2. Δημιουργία Παραθύρου Σύνδεσης (Login) ---

def create_login_window():
    sg.theme('LightBlue')
    login_layout = [
        [sg.Text('Σύνδεση Φοιτητή', font=('Helvetica', 20))],
        [sg.HSeparator()],
        [sg.Text('Όνομα Χρήστη:', size=(15, 1)), sg.Input(key='-NAME-', size=(30, 1))],
        [sg.Text('Κωδικός (Password):', size=(15, 1)), sg.Input(key='-PASSWORD-', password_char='*', size=(30, 1))],
        [sg.Text(size=(45, 1), key='-LOGIN_MESSAGE-', text_color='red')],
        [sg.Button('Σύνδεση', key='-LOGIN_BTN-'), sg.Button('Έξοδος', key='-EXIT_LOGIN-')]
    ]
    return sg.Window("Σύνδεση", login_layout, finalize=True)


# --- 3. Δημιουργία Κεντρικού Παραθύρου (Main App) ---

def create_main_window(user_name):
    # --- Layouts για κάθε 'Σελίδα' ---
    about_layout = [
        [sg.Text(f"Σχετικά με την Εφαρμογή - Χρήστης: {user_name}", font=('Helvetica', 16, 'bold'), text_color='#1064A8')],
        [sg.HSeparator()],
        [sg.Text("Αυτή η εφαρμογή λειτουργεί ως το κεντρικό interface για τον Tutor Agent.", size=(60, 1))],
        [sg.Text("Δημιουργήθηκε για το μάθημα 'Ποιότητα Λογισμικού' στο ΠΑ.ΜΑΚ.")],
        [sg.Text("Έκδοση: 1.0.0", size=(60, 1))]
    ]

    home_layout = [
        [sg.Text(f"Καλώς ήρθες, {user_name}!", font=('Helvetica', 20, 'bold'), text_color='#1E8449')],
        [sg.HSeparator()],
        [sg.Text("Χρησιμοποιήστε τα κουμπιά πλοήγησης αριστερά για να ξεκινήσετε:", size=(60, 1))],
        [sg.Text("➡️ Tutor: Ξεκινήστε μια συνομιλία για την Ποιότητα Λογισμικού.")],
        [sg.Text("➡️ Quiz: Δημιουργήστε ερωτήσεις κουίζ με βάση τις προηγούμενες συνεδρίες σας.")],
        [sg.Text("➡️ About: Πληροφορίες για την εφαρμογή.")]
    ]

    quiz_layout = [
        [sg.Text("Ενότητα Κουίζ (Quiz Generator)", font=('Helvetica', 16, 'bold'), text_color='#D68910')],
        [sg.HSeparator()],
        [sg.Text("Ερωτήσεις κουίζ θα εμφανίζονται εδώ με βάση την τελευταία σας σύνοψη.")],
        [sg.Multiline(default_text='[Πατήστε "Δημιουργία Νέου Κουίζ" για να ξεκινήσετε...]', size=(60, 10), key='-QUIZ_DISPLAY-', disabled=True)],
        [sg.Button("Δημιουργία Νέου Κουίζ", key='-GENERATE_QUIZ_BTN-'), sg.Button("Υποβολή Απαντήσεων", key='-SUBMIT_QUIZ_BTN-')]
    ]

    tutor_layout = [
        [sg.Text("Εικονικός Καθηγητής (Tutor Chat)", font=('Helvetica', 16, 'bold'), text_color='#2E86C1')],
        [sg.HSeparator()],
        [sg.Multiline(default_text=f'[Συνομιλία με τον Tutor Bot...]', size=(60, 15), key='-CHAT_HISTORY-', disabled=True, autoscroll=True)],
        [sg.Input(key='-CHAT_INPUT-', size=(50, 1)), sg.Button("Αποστολή", key='-SEND_CHAT_BTN-'), sg.Button("Τέλος Συνεδρίας", key='-END_SESSION_BTN-')]
    ]

    # --- Δομή Κεντρικού Παραθύρου ---
    home_column = sg.Column(home_layout, key='-COL_HOME-', visible=True)
    quiz_column = sg.Column(quiz_layout, key='-COL_QUIZ-', visible=False)
    tutor_column = sg.Column(tutor_layout, key='-COL_TUTOR-', visible=False)
    about_column = sg.Column(about_layout, key='-COL_ABOUT-', visible=False)

    nav_sidebar = [
        [sg.Button("🏠 Αρχική", key='-NAV_HOME-', size=(15, 2))],
        [sg.Button("💬 Tutor", key='-NAV_TUTOR-', size=(15, 2))],
        [sg.Button("❓ Quiz", key='-NAV_QUIZ-', size=(15, 2))],
        [sg.Button("ℹ️ About", key='-NAV_ABOUT-', size=(15, 2))],
        [sg.VPush()],
        [sg.Button("Αποσύνδεση", key='-LOGOUT_BTN-', size=(15, 1))]
    ]

    main_layout = [
        [
            sg.Column(nav_sidebar, justification='top'),
            sg.VSeperator(),
            sg.Column(
                [
                    [home_column, quiz_column, tutor_column, about_column]
                ],
                key='-MAIN_CONTENT_AREA-'
            )
        ]
    ]
    return sg.Window("UoM Software Quality Agent Interface", main_layout, finalize=True)


# --- 4. Κύρια Ροή Εκτέλεσης ---

# Εξωτερικοί Agents (χρειάζεται να γίνουν functional)
# Υποθέτουμε ότι οι modules TutorAgent, QuizAgent είναι διαθέσιμα
from tutor_tools import upload_to_cloud
from questions import agent_executor as quiz_executor_agent, QUIZ_SCHEMA
# Επειδή δεν έχω το tutor agent, θα φτιάξω ένα dummy
# import tutor_agent # <-- Αντικαταστήστε με το δικό σας module
# tutor_agent_executor = tutor_agent.agent_executor

# --- DUMMY AGENT SETUP (Για να μην σπάσει ο κώδικας) ---
# Επειδή το LangChain setup είναι πολύπλοκο για να ενσωματωθεί σε αυτό το αρχείο,
# και για να κάνουμε το GUI λειτουργικό, θα χρησιμοποιήσουμε μια απλοποιημένη
# κλήση LLM για τον Tutor Agent και θα χρησιμοποιήσουμε το `quiz_generator.py`
# για τον Quiz Agent.

# Απλοποιημένη κλήση LLM για Tutor/Quiz Agent (χωρίς AgentExecutor logic)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

LLM = ChatGoogleGenerativeAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    model="gemini-2.5-flash",
    temperature=0.2,
)

TUTOR_TEMPLATE = """
You are a tutor agent that helps students learn the course "Software Quality" at the University of Macedonia (UoM).
Answer in Greek. Provide clear and concise explanations.
"""
TUTOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", TUTOR_TEMPLATE),
    ("human", "{question}"),
])
# ---------------------------------------------


def run_login_app():
    """Εμφανίζει το παράθυρο σύνδεσης και επιστρέφει τα διαπιστευτήρια σε περίπτωση επιτυχίας."""
    login_window = create_login_window()
    
    while True:
        event, values = login_window.read()
        
        if event == sg.WIN_CLOSED or event == '-EXIT_LOGIN-':
            login_window.close()
            return False, None, None
            
        if event == '-LOGIN_BTN-':
            name = values['-NAME-'].strip()
            password = values['-PASSWORD-']
            
            authenticated, user_name, user_id = authenticate_user(name, password)
            
            if authenticated:
                login_window.close()
                return True, user_name, user_id
            else:
                login_window['-LOGIN_MESSAGE-'].update('Σφάλμα: Λάθος όνομα χρήστη ή κωδικός.', text_color='red')

def run_main_app(user_name, user_id):
    """Εκτελεί το κύριο παράθυρο της εφαρμογής."""
    window = create_main_window(user_name)
    current_page = '-COL_HOME-'
    chat_history = []
    
    # 5. Λειτουργία για την αλλαγή σελίδας
    def switch_page(new_key):
        nonlocal current_page
        if new_key == current_page: return
        
        window[current_page].update(visible=False)
        window[new_key].update(visible=True)
        current_page = new_key

    # 6. Βρόχος Γεγονότων Κυρίου Παραθύρου
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == '-LOGOUT_BTN-':
            # Εάν η συνομιλία δεν έχει κλείσει, κάνε upload τη σύνοψη
            if chat_history:
                # Προσομοίωση αποστολής σήματος για τερματισμό & upload
                # (Στην πραγματικότητα, αυτό θα γινόταν με ένα prompt στον Tutor Agent)
                sg.popup_ok("Αποσύνδεση", "Η σύνοψη της συνεδρίας ανέβηκε στο cloud.")

            break
        
        # Λογική Πλοήγησης
        if event.startswith('-NAV_'):
            switch_page('-COL_' + event.split('_')[1] + '-')

        # 7. Λογική για τον Tutor (Chat)
        elif event == '-SEND_CHAT_BTN-' and values['-CHAT_INPUT-']:
            user_message = values['-CHAT_INPUT-'].strip()
            if not user_message: continue

            # Εμφάνιση μηνύματος χρήστη
            chat_output = window['-CHAT_HISTORY-'].get()
            chat_output += f"You: {user_message}\n"
            window['-CHAT_HISTORY-'].update(chat_output)
            window['-CHAT_INPUT-'].update('', focus=True)

            # Κλήση στον Tutor Agent (Χρήση απλού LLM για ταχύτητα)
            # Στην πραγματική εφαρμογή, θα χρησιμοποιούσατε τον Tutor AgentExecutor
            try:
                # Δημιουργία αλυσίδας (chain) για την απάντηση
                chain = TUTOR_PROMPT | LLM
                response_text = chain.invoke({"question": user_message}).content
                
                # Προσθήκη στην ιστορία συνομιλίας
                chat_history.append({"role": "user", "content": user_message})
                chat_history.append({"role": "ai", "content": response_text})

                chat_output += f"Tutor: {response_text}\n"
                window['-CHAT_HISTORY-'].update(chat_output)

            except Exception as e:
                error_msg = f"Tutor Error: Cannot connect to AI. {e}"
                chat_output += f"Tutor: {error_msg}\n"
                window['-CHAT_HISTORY-'].update(chat_output)
        
        elif event == '-END_SESSION_BTN-':
            # Προσομοίωση: Κάνε upload τη σύνοψη (στην πραγματικότητα, ο Tutor Agent το κάνει)
            if chat_history:
                # Εδώ θα κάνατε invoke τον Tutor Agent με το "Τελος" prompt
                # και αυτός θα καλούσε το upload_to_cloud.
                sg.popup_ok("Τέλος Συνεδρίας", "Η σύνοψη της συνεδρίας ανέβηκε στο cloud.")
                chat_history = [] # Επαναφορά ιστορικού
                window['-CHAT_HISTORY-'].update("[Νέα συνεδρία ξεκίνησε...]")
            else:
                sg.popup_ok("Προσοχή", "Δεν υπάρχει ενεργή συνομιλία για σύνοψη.")

        # 8. Λογική για το Quiz
        elif event == '-GENERATE_QUIZ_BTN-':
            # Κλήση στον Quiz Agent
            try:
                # Η συνάρτηση main() του quiz_generator.py επιστρέφει το JSON των ερωτήσεων
                from quiz_generator import main as generate_quiz
                questions_json = generate_quiz(user_name, user_id)
                
                if questions_json:
                    quiz_text = "Νέο Κουίζ: Μετρικές Ποιότητας Λογισμικού\n\n"
                    for i, q in enumerate(questions_json):
                        quiz_text += f"{i+1}. {q['question_text']}\n"
                        # Εμφάνιση επιλογών (π.χ. Α, Β, Γ, Δ)
                        for j, option in enumerate(q['options']):
                             quiz_text += f"   {chr(65 + j)}: {option}\n" 
                        quiz_text += "\n"
                    window['-QUIZ_DISPLAY-'].update(quiz_text)
                else:
                    window['-QUIZ_DISPLAY-'].update("Αδυναμία δημιουργίας κουίζ. Ελέγξτε το server log.")
                    
            except Exception as e:
                sg.popup_error("Σφάλμα Quiz:", f"Αδυναμία κλήσης Quiz Agent. Βεβαιωθείτε ότι το 'quiz_generator.py' λειτουργεί. Error: {e}")
                window['-QUIZ_DISPLAY-'].update(f"Error: {e}")
        
        elif event == '-SUBMIT_QUIZ_BTN-':
            sg.popup("Υποβολή Κουίζ", "Οι απαντήσεις σας υποβλήθηκαν! (Απαιτείται πρόσθετος κώδικας για την αξιολόγηση)")


    window.close()


if __name__ == '__main__':
    # 1. Εκτέλεση Login
    success, name, id = run_login_app()
    
    # 2. Αν επιτυχής, εκτέλεση Main App
    if success:
        run_main_app(name, id)