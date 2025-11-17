import os  
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from dotenv import load_dotenv  
from vector import get_retriever
load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    api_key=api_key,
    model="gemini-2.5-flash",
    temperature=0.2,
)
prompt = """
Μπορεις να απαντησεις στα ελληνικα.
Σαν προτη γλωσσα επιλεξε τα οτι γλωσσα μιληση πρωτα ο χρηστης.

You are a tutor bot that helps students learn The subject of Artificial Intelligence.
Provide clear and concise explanations, examples, and answer any questions they may have about AI concepts, techniques, and applications.
Focus on making complex topics understandable and engaging for learners of all levels.

if the question is not in the vector database, respond with "I'm sorry, I don't have the information on that topic."

Here is the vector database retriever that contains relevant information about AI:
{retriever_code}

Please answer the following question:{question}

Here is the history of the conversation so far:{chat_history}

Answer:


"""
def generate_tutor_response(question, chat_history):
    retriever = get_retriever(search_k=question)
    retriever_code = f"retriever = {retriever}"
    formatted_prompt = prompt.format(retriever_code=retriever_code,question=question, chat_history=chat_history)
    print("Things are working up to here")
    response = llm.invoke(formatted_prompt)
    return response.content


def chat():
    chat_history = ""
    print("Welcome to the AI Tutor Bot! Type 'exit' to end the session.")
    while True:
        question = input("You: ")
        if question.lower() == 'exit':
            print("Ending the session. Goodbye!")
            break
        response = generate_tutor_response(question, chat_history)
        print(f"Tutor Bot: {response}")
        chat_history += f"\nYou: {question}\nTutor Bot: {response}"

if __name__ == "__main__":
    chat()