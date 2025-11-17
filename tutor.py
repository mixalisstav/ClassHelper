import os  
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from dotenv import load_dotenv  
load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    api_key=api_key,
    model="gemini-2.5-flash",
    temperature=0.2,
)
prompt = """
Μπορεις να απαντησεις στα ελληνικα.
Σαν προτη γλωσσα επιλεξε τα οτι γλωσσα επιλαξει ο χρηστης.

You are a tutor bot that helps students learn The subject of Artificial Intelligence.
Provide clear and concise explanations, examples, and answer any questions they may have about AI concepts, techniques, and applications.
Focus on making complex topics understandable and engaging for learners of all levels.

You will answer the questions only from the vector database provided. If the answer is not contained within the context, respond with "I don't know."


Please answer the following question:{question}

Here is the history of the conversation so far:{chat_history}

Answer:


"""
c_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "You are a tutor bot that helps students learn The subject of Artificial Intelligence. "
        "Provide clear and concise explanations, examples, and answer any questions they may have about AI concepts, techniques, and applications. "
        "Focus on making complex topics understandable and engaging for learners of all levels."
    ),
    HumanMessagePromptTemplate.from_template(
        "You will answer the questions only from the vector database provided. If the answer is not contained within the context, respond with 'I don't know.'\n\n"
        "Please answer the following question:{question}\n\n"
        "Here is the history of the conversation so far:{chat_history}\n\n"
        "Answer:"
    ),
])





def generate_tutor_response(question, chat_history):
    formatted_prompt = prompt.format(question=question, chat_history=chat_history)
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