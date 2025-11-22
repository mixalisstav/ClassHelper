import FreeSimpleGUI as sg
import pandas as pd
import sqlite3 as sql
import os
from dotenv import load_dotenv
load_dotenv()
   

# --- Εισαγωγή Εξωτερικών Modules ---
try:
    from questions import main as generate_quiz
except ImportError:
    generate_quiz = None
    print("Προσοχή: Το αρχείο 'questions.py' δεν βρέθηκε.")

# --- AI SETUP (Για το Tutor Chat) ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate


# --- 1. Λειτουργίες Πιστοποίησης & Βάσης Δεδομένων ---

def ensure_student_in_db(name, id):
    """Εισάγει τον χρήστη στον πίνακα students αν δεν υπάρχει."""
    try:
        conn = sql.connect('classroom.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS students 
                     (name TEXT, id TEXT, questions TEXT)''')
        c.execute('''SELECT name FROM students WHERE name=? AND id=?''', (name, id))
        result = c.fetchone()
        if result is None:
            c.execute('''INSERT INTO students (name, id, questions) VALUES (?, ?, ?)''', (name, id, '{}'))
            conn.commit()
        c.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

def authenticate_user(name, password):
    """Ελέγχει τα διαπιστευτήρια του χρήστη έναντι του users.csv."""
    try:
        users_df = pd.read_csv('users.csv')
        users_df.columns = users_df.columns.str.strip()
        
        if 'user_name' not in users_df.columns or 'user_password' not in users_df.columns or 'id' not in users_df.columns:
            sg.popup_error("Σφάλμα:", "Το csv πρέπει να έχει στήλες: user_name, user_password, id")
            return False, None, None

        match = users_df[(users_df['user_name'].astype(str) == name) & (users_df['user_password'].astype(str) == password)]
        
        if not match.empty:
            user_id = str(match['id'].iloc[0])
            ensure_student_in_db(name, user_id)
            return True, name, user_id
        else:
            return False, None, None
    except FileNotFoundError:
        sg.popup_error("Σφάλμα", "Δεν βρέθηκε το αρχείο users.csv")
        return False, None, None
    except Exception as e:
        sg.popup_error("Σφάλμα", f"Λάθος κατά την ανάγνωση του csv: {e}")
        return False, None, None


# --- 2. Σχεδιασμός GUI (Layouts) ---

def create_login_window():
    sg.theme('DefaultNoMoreNagging') 
    layout = [
        [sg.Text('Σύνδεση Φοιτητή', font=('Helvetica', 20), text_color='#2C3E50')],
        [sg.HSeparator()],
        [sg.Text('Όνομα:', size=(10, 1)), sg.Input(key='-USER-', size=(25, 1))],
        [sg.Text('Κωδικός:', size=(10, 1)), sg.Input(key='-PASS-', password_char='*', size=(25, 1))],
        [sg.Text('', key='-MSG-', text_color='red', size=(35, 1))],
        [sg.Button('Είσοδος', key='-LOGIN-', bind_return_key=True), sg.Button('Έξοδος', key='-EXIT-')]
    ]
    return sg.Window('Login - Tutor Agent', layout, finalize=True)

def create_main_window(user_name):
    sg.theme('DefaultNoMoreNagging')
    
    home_layout = [
        [sg.Text(f"Καλώς ήρθες, {user_name}!", font=('Helvetica', 22, 'bold'), text_color='#27AE60')],
        [sg.HSeparator()],
        [sg.Text("Επιλέξτε μια λειτουργία από το μενού αριστερά:", font=('Helvetica', 12))],
        [sg.Text("💬 Tutor: Συζήτηση για το μάθημα.")],
        [sg.Text("❓ Quiz: Τεστ γνώσεων με βάση τη συζήτηση.")]
    ]
    
    tutor_layout = [
        [sg.Text("Tutor Chat", font=('Helvetica', 18, 'bold'), text_color='#2980B9')],
        [sg.Multiline(size=(60, 20), key='-CHAT_BOX-', disabled=True, autoscroll=True, font=('Courier', 10))],
        [sg.Input(key='-CHAT_INPUT-', size=(50, 1)), sg.Button('Αποστολή', key='-SEND-', bind_return_key=True)],
        [sg.Button('Τέλος Συνεδρίας (Upload Summary)', key='-END_SESSION-')]
    ]
    
    quiz_layout = [
        [sg.Text("Quiz Generator", font=('Helvetica', 18, 'bold'), text_color='#D35400')],
        [sg.Text("Πατήστε το κουμπί για να δημιουργηθεί το κουίζ βάσει του ιστορικού σας.")],
        [sg.Button("Δημιουργία Κουίζ", key='-GEN_QUIZ-')],
        [sg.Multiline("Τα ερωτήματα θα εμφανιστούν εδώ...", size=(60, 20), key='-QUIZ_BOX-', disabled=True, font=('Courier', 10))]
    ]
    
    about_layout = [
        [sg.Text("Σχετικά", font=('Helvetica', 18, 'bold'))],
        [sg.Text("Εφαρμογή Tutor Agent & Quiz Generator")],
        [sg.Text("Μάθημα: Ποιότητα Λογισμικού (ΠΑΜΑΚ)")]
    ]

    sidebar = [
        [sg.Text("Μενού", font=('Helvetica', 14, 'bold'))],
        [sg.Button("🏠 Αρχική", key='-NAV_HOME-', size=(12, 2))],
        [sg.Button("💬 Tutor", key='-NAV_TUTOR-', size=(12, 2))],
        [sg.Button("❓ Quiz", key='-NAV_QUIZ-', size=(12, 2))],
        [sg.Button("ℹ️ About", key='-NAV_ABOUT-', size=(12, 2))],
        [sg.VPush()],
        [sg.Button("Logout", key='-LOGOUT-', size=(12, 1))]
    ]

    main_col = sg.Column([
        [sg.Column(home_layout, key='-COL_HOME-', visible=True),
         sg.Column(tutor_layout, key='-COL_TUTOR-', visible=False),
         sg.Column(quiz_layout, key='-COL_QUIZ-', visible=False),
         sg.Column(about_layout, key='-COL_ABOUT-', visible=False)]
    ])

    layout = [[sg.Column(sidebar, element_justification='c', vertical_alignment='top'), sg.VSeparator(), main_col]]

    return sg.Window('UoM Tutor Interface', layout, size=(800, 600), finalize=True)


# --- 3. Κύρια Λογική (Main Loop) ---

def run_application():
    window = create_login_window()
    user_name = None
    user_id = None
    
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, '-EXIT-'):
            window.close()
            return
        
        if event == '-LOGIN-':
            success, name, uid = authenticate_user(values['-USER-'], values['-PASS-'])
            if success:
                user_name = name
                user_id = uid
                window.close()
                break
            else:
                window['-MSG-'].update("Λάθος στοιχεία ή ανύπαρκτος χρήστης.")

    window = create_main_window(user_name)
    current_page = '-COL_HOME-'
    chat_history_text = ""
    from langchain.schema import HumanMessage, AIMessage
    chat_history = []
    chat_history.append(HumanMessage(content=f"Το ονομα μου ειναι {user_name}\nΟ αριθμος μητρου μου ειναι: {user_id}\nΠροηγουμενες ερωτησεις μου ειναι: "))
    chat_history.append(AIMessage(content=""))
    while True:
        event, values = window.read()
        
        
        if event in (sg.WIN_CLOSED, '-LOGOUT-'):
            break
            
        # --- NAVIGATION LOGIC ---
        if event.startswith('-NAV_'):
            target = event.replace('NAV', 'COL')
            
            if target != current_page:
                window[current_page].update(visible=False)
                window[target].update(visible=True)
                current_page = target
        
        if event == '-SEND-':
            user_input = values['-CHAT_INPUT-'].strip()
            if user_input:
                chat_history_text += f"You: {user_input}\n"
                window['-CHAT_BOX-'].update(chat_history_text)
                window['-CHAT_INPUT-'].update('')
                from tutor import generate_tutor_response,create_agent_executor
                flag = create_agent_executor()
                if flag:
                    try:
                        response = generate_tutor_response(user_input, chat_history=chat_history)
                        ai_msg = response
                        chat_history_text += f"Tutor: {ai_msg}\n\n"
                        window['-CHAT_BOX-'].update(chat_history_text)
                        chat_history.append(HumanMessage(content=user_input))
                        chat_history.append(AIMessage(content=ai_msg))
                    except Exception as e:
                        chat_history_text += f"System Error: {str(e)}\n"
                        window['-CHAT_BOX-'].update(chat_history_text)
                else:
                    chat_history_text += "System: Το AI δεν είναι συνδεδεμένο.\n"
                    window['-CHAT_BOX-'].update(chat_history_text)
        
        if event == '-END_SESSION-':
            sg.popup("Ενημέρωση", "Η συνεδρία ολοκληρώθηκε και η σύνοψη αποθηκεύτηκε.")
            chat_history_text = ""
            window['-CHAT_BOX-'].update("Ξεκινήστε νέα συζήτηση...")
            from tutor import create_agent_executor
            question="Τελος"
            generate_tutor_response(question=question, chat_history=chat_history)

        if event == '-GEN_QUIZ-':
            if generate_quiz:
                try:
                    window['-QUIZ_BOX-'].update("Γίνεται ανάλυση ιστορικού και δημιουργία ερωτήσεων...\nΠαρακαλώ περιμένετε.")
                    window.refresh()
                    
                    questions = generate_quiz(user_name, user_id)
                    
                    if questions:
                        display_text = f"ΚΟΥΙΖ ΓΙΑ ΤΟΝ ΦΟΙΤΗΤΗ: {user_name}\n{'='*40}\n\n"
                        for idx, q in enumerate(questions, 1):
                            display_text += f"{idx}. {q['question_text']}\n"
                            for opt_idx, option in enumerate(q['options']):
                                letter = chr(65 + opt_idx)
                                display_text += f"   {letter}. {option}\n"
                            display_text += "\n"
                        window['-QUIZ_BOX-'].update(display_text)
                    else:
                        window['-QUIZ_BOX-'].update("Δεν βρέθηκαν δεδομένα για δημιουργία κουίζ.")
                except Exception as e:
                     window['-QUIZ_BOX-'].update(f"Σφάλμα κατά τη δημιουργία κουίζ: {e}")
            else:
                 window['-QUIZ_BOX-'].update("Το αρχείο questions.py λείπει.")

    window.close()

if __name__ == "__main__":
    run_application()