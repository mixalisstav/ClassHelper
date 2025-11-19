from langchain.agents import tool
from vector import get_retriever
from langchain.schema import HumanMessage

@tool("cloud", return_direct=True)
def upload_to_cloud(data,history):
    """Here you can upload the most asked questions to the cloud.Using the database classroom."""
    try:
        print("Uploading data to the cloud...")
        print(data)
        return"Data uploaded to the cloud successfully."
    except Exception as e:
        print(f"An error occurred while uploading data: {e}")
        
        
@tool("most_frequent_questions")
def get_most_frequent_questions(history, top_n=5):
    """Here you can get the most frequently asked questions from the chat history."""
    question_count = {}
    for message in history:
        if isinstance(message, HumanMessage):
            if message.content in question_count:
                question_count[message.content] += 1
            else:
                question_count[message.content] = 1
    sorted_questions = sorted(question_count.items(), key=lambda x: x[1], reverse=True)
    most_frequent = [q for q, count in sorted_questions[:top_n]]
    return most_frequent
    
    
    
def temp(chat_history):
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

