import FreeSimpleGUI as sg
import pandas as pd
import sqlite3 as sql
import os
from dotenv import load_dotenv
from langchain.schema import HumanMessage, AIMessage
import sys
import os

def resource_path(relative_path):
    """ Επιστρέφει το απόλυτο path για πόρους, είτε τρέχει ως script είτε ως exe """
    try:
        # Το PyInstaller δημιουργεί έναν προσωρινό φάκελο στο _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Φορτώνει μεταβλητές περιβάλλοντος
load_dotenv()

# --- Εισαγωγή Εξωτερικών Modules ---
# Προσπαθούμε να εισάγουμε το questions.py
try:
    from questions import main as generate_quiz
except ImportError:
    generate_quiz = None
    print("Προσοχή: Το αρχείο 'questions.py' δεν βρέθηκε.")

# Προσπάθεια εισαγωγής από το tutor.py
try:
    from tutor import generate_tutor_response, create_agent_executor
except ImportError:
    print("Προσοχή: Το αρχείο 'tutor.py' δεν βρέθηκε ή έχει λάθη.")
    generate_tutor_response = None
    create_agent_executor = None


# --- 1. Λειτουργίες Πιστοποίησης & Βάσης Δεδομένων ---

def ensure_student_in_db(name, id):
    """Εισάγει τον χρήστη στον πίνακα students αν δεν υπάρχει."""
    try:
        # ΝΕΟ: Η βάση δεδομένων θα αποθηκεύεται στον φάκελο του χρήστη ή δίπλα στο App
        db_path = os.path.join(os.path.expanduser("~"), "classroom.db") 
        conn = sql.connect(db_path)
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
        # Καθαρισμός ονομάτων στηλών (αφαίρεση κενών)
        users_df.columns = users_df.columns.str.strip()
        
        # Αυτόματη αναγνώριση ονομάτων στηλών (αν είναι name ή user_name)
        if 'name' in users_df.columns:
             user_col = 'name'
             pass_col = 'password'
        elif 'user_name' in users_df.columns:
             user_col = 'user_name'
             pass_col = 'user_password'
        else:
            sg.popup_error("Σφάλμα:", "Το csv πρέπει να έχει στήλες: name (ή user_name), password, id")
            return False, None, None

        # Έλεγχος στοιχείων
        match = users_df[(users_df[user_col].astype(str) == name) & (users_df[pass_col].astype(str) == password)]
        
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


# --- 2. Νέα Λειτουργία: Παράθυρο Εξέτασης (Dynamic Quiz) ---

def run_quiz_window(questions):
    """Δημιουργεί ένα δυναμικό παράθυρο με Radio buttons για τις ερωτήσεις."""
    
    sg.theme('DefaultNoMoreNagging')
    quiz_content = []
    
    # Δημιουργία διάταξης (Layout) δυναμικά βάσει των ερωτήσεων
    for idx, q in enumerate(questions):
        # Κείμενο ερώτησης
        quiz_content.append([sg.Text(f"{idx+1}. {q['question_text']}", font=('Helvetica', 11, 'bold'), text_color='#2C3E50', size=(80, None))])
        
        # Radio Buttons (Ομαδοποιημένα ανά ερώτηση με group_id=idx)
        # Το κλειδί (key) είναι tuple: (αριθμός ερώτησης, κείμενο επιλογής)
        for opt in q['options']:
            quiz_content.append([sg.Radio(opt, group_id=idx, key=(idx, opt), font=('Helvetica', 10))])
        
        quiz_content.append([sg.HorizontalSeparator()])

    # Κουμπί Υποβολής στο τέλος
    quiz_content.append([sg.Push(), sg.Button('Υποβολή Απαντήσεων', key='-SUBMIT_QUIZ-', size=(20, 2), button_color='#27AE60'), sg.Push()])

    # Τοποθέτηση σε Scrollable Column (γιατί μπορεί να είναι πολλές οι ερωτήσεις)
    layout = [
        [sg.Column(quiz_content, scrollable=True, vertical_scroll_only=True, size=(800, 500), key='-QUIZ_SCROLL-')]
    ]

    window = sg.Window('Εξέταση Κουίζ', layout, modal=True, finalize=True)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        
        if event == '-SUBMIT_QUIZ-':
            score = 0
            total = len(questions)
            results_text = ""
            
            # Υπολογισμός Σκορ
            for idx, q in enumerate(questions):
                user_answer = None
                
                # Βρίσκουμε ποιο Radio είναι επιλεγμένο (True) για αυτή την ερώτηση
                for opt in q['options']:
                    if values.get((idx, opt)) is True:
                        user_answer = opt
                        break
                
                correct_answer = q['correct_answer']
                
                if user_answer == correct_answer:
                    score += 1
                    results_text += f"✅ Ερώτηση {idx+1}: Σωστό!\n"
                else:
                    results_text += f"❌ Ερώτηση {idx+1}: Λάθος.\n"
                    results_text += f"   Η απάντησή σας: {user_answer if user_answer else 'Καμία'}\n"
                    results_text += f"   Σωστή απάντηση: {correct_answer}\n"
                results_text += "-"*40 + "\n"
            
            # Εμφάνιση Αποτελεσμάτων
            percentage = (score / total) * 100
            msg_title = "Αποτελέσματα Κουίζ"
            msg_body = f"Σκορ: {score} / {total} ({percentage:.1f}%)\n\nΑναλυτικά:\n{results_text}"
            
            sg.popup_scrolled(msg_body, title=msg_title, size=(60, 30))
            break # Κλείσιμο παραθύρου κουίζ μετά την υποβολή
            
    window.close()


# --- 3. Σχεδιασμός Κεντρικού GUI ---

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
        [sg.Text("❓ Quiz: Τεστ γνώσεων με Radio buttons και βαθμολόγηση.")]
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
        [sg.Text("Θα ανοίξει νέο παράθυρο με τις ερωτήσεις.", text_color='gray')],
        [sg.Button("Δημιουργία & Έναρξη Κουίζ", key='-GEN_QUIZ-', size=(25, 2), button_color='#D35400')],
        [sg.Text("", key='-QUIZ_STATUS-', size=(50, 2), text_color='blue')]
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

    # Κεντρική στήλη με όλες τις 'σελίδες'
    main_col = sg.Column([
        [sg.Column(home_layout, key='-COL_HOME-', visible=True),
         sg.Column(tutor_layout, key='-COL_TUTOR-', visible=False),
         sg.Column(quiz_layout, key='-COL_QUIZ-', visible=False),
         sg.Column(about_layout, key='-COL_ABOUT-', visible=False)]
    ])

    layout = [[sg.Column(sidebar, element_justification='c', vertical_alignment='top'), sg.VSeparator(), main_col]]

    return sg.Window('UoM Tutor Interface', layout, size=(900, 600), finalize=True)


# --- 4. Κύρια Λογική (Main Loop) ---

def run_application():
    # --- Φάση 1: Login ---
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

    # --- Φάση 2: Main Application ---
    window = create_main_window(user_name)
    current_page = '-COL_HOME-'
    
    # Αρχικοποίηση Chat History
    chat_history_text = ""
    chat_history = []
    # Προσθέτουμε το αρχικό μήνυμα για τον agent context
    chat_history.append(HumanMessage(content=f"Το ονομα μου ειναι {user_name}\nΟ αριθμος μητρωου μου ειναι: {user_id}"))
    chat_history.append(AIMessage(content=""))

    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, '-LOGOUT-'):
            break
            
        # --- NAVIGATION LOGIC ---
        if event.startswith('-NAV_'):
            # Αντικατάσταση NAV με COL για να βρούμε το σωστό κλειδί (π.χ. -NAV_HOME- -> -COL_HOME-)
            target = event.replace('NAV', 'COL')
            
            if target != current_page:
                window[current_page].update(visible=False)
                window[target].update(visible=True)
                current_page = target
        
        # --- TUTOR LOGIC ---
        if event == '-SEND-':
            user_input = values['-CHAT_INPUT-'].strip()
            if user_input:
                # 1. Ενημέρωση GUI
                chat_history_text += f"You: {user_input}\n"
                window['-CHAT_BOX-'].update(chat_history_text)
                window['-CHAT_INPUT-'].update('')
                
                # 2. Κλήση Agent
                if create_agent_executor and generate_tutor_response:
                    flag = create_agent_executor() 
                    if flag:
                        try:
                            # Κλήση της συνάρτησης από το tutor.py
                            response = generate_tutor_response(user_input, chat_history=chat_history)
                            ai_msg = str(response)
                            chat_history_text += f"Tutor: {ai_msg}\n\n"
                            window['-CHAT_BOX-'].update(chat_history_text)
                            
                            # Ενημέρωση ιστορικού για το session
                            chat_history.append(HumanMessage(content=user_input))
                            chat_history.append(AIMessage(content=ai_msg))
                        except Exception as e:
                            chat_history_text += f"System Error: {str(e)}\n"
                            window['-CHAT_BOX-'].update(chat_history_text)
                    else:
                         window['-CHAT_BOX-'].update(chat_history_text + "System: Αποτυχία σύνδεσης Agent.\n")
                else:
                    window['-CHAT_BOX-'].update(chat_history_text + "System: Modules not loaded (tutor.py missing).\n")
        
        if event == '-END_SESSION-':
            sg.popup("Ενημέρωση", "Η συνεδρία ολοκληρώθηκε. Η σύνοψη ανεβαίνει στο cloud...")
            chat_history_text = ""
            window['-CHAT_BOX-'].update("Ξεκινήστε νέα συζήτηση...")
            
            # Κλήση upload μέσω του "Τελος"
            if generate_tutor_response:
                try:
                    generate_tutor_response(question="Τελος", chat_history=chat_history)
                except Exception as e:
                    print(f"Error uploading summary: {e}")
            
            # Reset chat history
            chat_history = []
            chat_history.append(HumanMessage(content=f"Το ονομα μου ειναι {user_name}\nΟ αριθμος μητρωου μου ειναι: {user_id}"))
            chat_history.append(AIMessage(content=""))

        # --- QUIZ LOGIC (Με νέο παράθυρο) ---
        if event == '-GEN_QUIZ-':
            if generate_quiz:
                try:
                    window['-QUIZ_STATUS-'].update("Δημιουργία ερωτήσεων... Παρακαλώ περιμένετε.")
                    window.refresh()
                    
                    # 1. Λήψη ερωτήσεων (JSON) από το questions.py
                    questions = generate_quiz(user_name, user_id)
                    
                    if questions and isinstance(questions, list) and len(questions) > 0:
                        window['-QUIZ_STATUS-'].update("Το κουίζ ξεκίνησε!")
                        # 2. Άνοιγμα του νέου παραθύρου εξέτασης
                        run_quiz_window(questions)
                        window['-QUIZ_STATUS-'].update("Το κουίζ ολοκληρώθηκε.")
                    else:
                        window['-QUIZ_STATUS-'].update("Δεν βρέθηκαν ερωτήσεις.")
                        sg.popup("Πληροφορία", "Δεν υπάρχουν αρκετά δεδομένα για κουίζ.\nΜιλήστε πρώτα με τον Tutor και κλείστε τη συνεδρία.")
                except Exception as e:
                     window['-QUIZ_STATUS-'].update("Σφάλμα.")
                     sg.popup_error(f"Σφάλμα: {e}")
            else:
                 sg.popup_error("Το αρχείο questions.py λείπει.")

    window.close()

if __name__ == "__main__":
    run_application()