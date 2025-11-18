from langchain.agents import tool
from vector import get_retriever

@tool("cloud", return_direct=True)
def upload_to_cloud(data: str) -> str:
    """Here you can implement the logic to upload data to the cloud."""
    # Simulate uploading data to the cloud
    print("Uploading the following data to the cloud:")
    print(data)
    return "Data uploaded to the cloud successfully."

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

