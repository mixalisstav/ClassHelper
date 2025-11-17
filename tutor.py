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
Μπορεις να απαντησεις στα ελληνικα.
Σαν προτη γλωσσα επιλεξε τα οτι γλωσσα μιληση πρωτα ο χρηστης.

You are a tutor agent that helps students learn The class of Ποιοτητα λογισμικου(Software Quality) in a Uom.
Provide clear and concise explanations, examples, and answer any questions.
Focus on making complex topics understandable and engaging for learners of all levels.

with your tools you can (only from the vector database: 
- Retrieve relevant information from a knowledge base about Ποιοτητα λογισμικου(Software Quality) using the "vector_db" tool.
- Provide examples and explanations of AI concepts.

At the end of the session:
- Summarize the key points discussed,and using the tool ="cloud", up load to the cloud the most asked questions.
"""
prompt = ChatPromptTemplate.from_messages([
    ("system",TEMPLATE),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human","{question}"),
    MessagesPlaceholder("agent_scratchpad"),
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
    final = find(question,response['output'])
    return final


TEMPLATE2 = "You will extract the important information from the following documents to answer the question."
def find(question,lista):
    llm2 = ChatGoogleGenerativeAI(
        api_key=api_key,
        model="gemini-2.5-flash",
        temperature=0.2,
    )
    agent2 = create_openai_tools_agent(
        llm=llm2,
        tools=[],
        prompt=ChatPromptTemplate.from_messages([
            ("system",TEMPLATE2),
            ("human","{question}"),
            ("human","{lista}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        )
    agent_executor2 = AgentExecutor.from_agent_and_tools(
        agent=agent2,
        tools=[],
        verbose=True,
    )
    information = agent_executor2.invoke(
        input={
            "question": question,
            "lista": lista,
           }
    )
    
    
    return information


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

if __name__ == "__main__":
    chat()
