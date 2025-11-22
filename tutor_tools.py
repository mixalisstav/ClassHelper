from langchain.agents import tool
from vector import get_retriever
from langchain.schema import HumanMessage
import os

@tool("cloud", return_direct=True)
def upload_to_cloud(summarization,name,id):
    """Here you can upload the summarization to the cloud.Using the database classroom.db and you will need the student's name."""
    try:
        import sqlite3 as sql
        # ΝΕΟ: Η βάση δεδομένων θα αποθηκεύεται στον φάκελο του χρήστη ή δίπλα στο App
        db_path = os.path.join(os.path.expanduser("~"), "classroom.db") 
        conn = sql.connect(db_path)     
        c = conn.cursor()
        
        student_name = name
        c.execute(
            "UPDATE students SET questions = ? WHERE name = ? AND id=?", # Correct UPDATE syntax
            (str(summarization), student_name, id)
        )
        conn.commit()
        c.close()
        conn.close()
        return "Data uploaded successfully."
    except Exception as e:
        print(f"An error occurred while uploading data: {e}")
        
        
@tool("get_most_frequent_questions")
def get_most_frequent_questions(name,history):
    """Here you can get the most frequently asked questions from the chat history."""
    import sqlite3 as sql
    import json
    conn = sql.connect('classroom.db')
    c = conn.cursor()
    # Fetch all student records
    c.execute("SELECT questions FROM students WHERE name=?", (name,))
    question_count = c.fetchall()
    question_count = question_count[0][0] if question_count else "{}"
    question_count = json.loads(question_count.replace("'", '"'))
    c.close()
    conn.close()
    for message in history:
        if isinstance(message, HumanMessage):
            if message.content in question_count:
                question_count[message.content] += 1
            else:
                question_count[message.content] = 1
    sorted_questions = sorted(question_count.items(), key=lambda x: x[1], reverse=True)
    print(sorted_questions)
    return sorted_questions
    
        

@tool("vector_db")
def retrieve_from_vector_db(query: str) -> str:
    """Retrieve relevant documents from the vector database based on the query."""
    retriever = get_retriever()
    results = retriever.get_relevant_documents(query)

    if not results:
        return "No relevant documents found."

    combined_results = "\n\n".join(
        [
            f"Document {i+1}:\n{doc.page_content}"
            for i, doc in enumerate(results)
        ]
    )
    return combined_results

