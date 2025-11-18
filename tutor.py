import os  
from dotenv import load_dotenv

from langchain.agents import create_openai_tools_agent,AgentExecutor,tool

from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate,MessagesPlaceholder
from dotenv import load_dotenv

from tutor_tools import upload_to_cloud, retrieve_from_vector_db
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
- Upload the most frequently asked questions to the cloud using the tool "cloud".
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", TEMPLATE),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

tools = [upload_to_cloud, retrieve_from_vector_db]
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



def chat():
    chat_history = []
    print("Welcome to the AI Tutor Bot! Type 'exit' to end the session.")
    while True:
        question = input("You: ")
        if question.lower() == 'q':
            print("Ending the session. Goodbye!")
            agent_executor.invoke(input={"question": "Upload the most asked questions to the cloud.", "chat_history": chat_history})
            break
        response = str(generate_tutor_response(question, chat_history))
        print(f"Tutor Bot: {response}")
        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=response))
        
        # check frquency of questions in chat_history
        question_count = {}
        for message in chat_history:
            if isinstance(message, HumanMessage):
                if message.content in question_count:
                    question_count[message.content] += 1
                else:
                    question_count[message.content] = 1
        # Print the most frequently asked questions
        sorted_questions = sorted(question_count.items(), key=lambda x: x[1], reverse=True)
        print("Most frequently asked questions so far:")
        for question, count in sorted_questions[:5]:
            print(f"'{question}' asked {count} times")  

if __name__ == "__main__":
    chat()
