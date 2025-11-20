import os  
from dotenv import load_dotenv

from langchain.agents import create_openai_tools_agent,AgentExecutor,tool

from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate,MessagesPlaceholder
from dotenv import load_dotenv

from tutor_tools import upload_to_cloud, retrieve_from_vector_db, get_most_frequent_questions
from langchain_google_genai import ChatGoogleGenerativeAI
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    api_key=api_key,
    model="gemini-2.5-flash",
    temperature=0.2,
)
TEMPLATE = """
Μπορείς να απαντάς στα ελληνικά.
Ως κύρια γλώσσα απάντησης να επιλέγεις πάντα αυτήν που χρησιμοποίησε πρώτα ο χρήστης.

You are a tutor agent that helps students learn the course 
"Ποιότητα Λογισμικού (Software Quality)" at the University of Macedonia (UoM).

Your goals:
- Provide clear and concise explanations.
- Use examples, analogies, and step-by-step reasoning.
- Make complex topics simple and engaging for students of all levels.

Tool usage rules:
- You may retrieve information ONLY from the vector database using the tool "vector_db".
- Use the retrieved information to answer questions related to Software Quality.
- You may also generate explanations and examples based on general AI knowledge.

End of session:
- Summarize the key points discussed.
- Upload the summarization to the cloud using the tool "cloud".
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", TEMPLATE),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

tools = [upload_to_cloud, retrieve_from_vector_db,get_most_frequent_questions]
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

def generate_tutor_response(question, chat_history):
    
    print("Things are working up to here")
    response = agent_executor.invoke(
        input={
            "question": question,
            "chat_history": chat_history,
            }
        )
    
    return response['output']



def chat(name,id):
    import sqlite3 as sql
    conn = sql.connect('classroom.db')
    c = conn.cursor()
    c.execute('''SELECT questions FROM students WHERE name=?''', (name,))
    result = c.fetchone()
    if result is None:
        c.execute('''INSERT INTO students (name, questions) VALUES (?, ?)''', (name, ''))
    conn.commit()
    c.close()
    conn.close()
    chat_history = []
    chat_history.append(HumanMessage(content=f"Το ονομα μου ειναι {name}\nΟ αριθμος μητρου μου ειναι: {id}\nΠροηγουμενες ερωτησεις μου ειναι: {result[0]}"))
    chat_history.append(AIMessage(content=""))
    
    print(f"Welcome {name} to the AI Tutor Bot! Type 'exit' to end the session.")
    while True:
        question = input("You: ")
        if question.lower() in ['q','exit','quit','Τελος','τέλος','σταμάτα','τελος']:
            print("Ending the session. Goodbye!")
            agent_executor.invoke(input={"question": "Τελος", "chat_history": chat_history})
            break
        response = str(generate_tutor_response(question, chat_history))
        print(f"Tutor Bot: {response}")
        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=response))

 

 
 
def get_user_credentials():
    import pandas as pd
    name = input("Enter your name: ")
    password= input("Enter your password: ")
    users_df = pd.read_csv('users.csv')
    users = users_df.values.tolist()
    authenticated = False
    for user in users:
        user_name, user_password, id = user
        if name == user_name and password == user_password:
            authenticated = True
            break
    if authenticated:
        return True,name,id
    else:
        return False,"noname","noid"
        
if __name__ == "__main__":
    trig,name,id= get_user_credentials()
    
    if trig: 
        chat(name=name,id=id)
    else:
        print("Authentication failed. Exiting the program.")    
    
    
    
