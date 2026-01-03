import gradio as gr
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import ollama

# Step 1: Define static summaries (simulate context for testing)
summaries = [
    "From April to June 2024, total sales in Downtown were $15,000.",
    "From April to June 2024, total sales in Uptown were $12,500.",
    "From April to June 2024, total sales in Midtown were $18,750.",
]

# Step 2: Generate sentence embeddings
embedder = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = embedder.encode(summaries)

# Step 3: Build FAISS index
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# Step 4: Define the query function
def generate_answer_with_llama3(query):
    query_embedding = embedder.encode([query])
    _, I = index.search(query_embedding, k=3)
    context = "\n".join([summaries[i] for i in I[0]])

    prompt = f"""Answer the following query based on the sales context below.

Query: {query}

Context:
{context}

Answer:"""

    response = ollama.chat(
        model='llama3',  # You can use 'mistral' if llama3 is too heavy
        messages=[
            {"role": "system", "content": "You are a helpful assistant for a CEO analyzing burger sales."},
            {"role": "user", "content": prompt}
        ]
    )

    return response['message']['content']

# Step 5: Gradio UI function
def rag_query_ui(user_input):
    try:
        return generate_answer_with_llama3(user_input)
    except Exception as e:
        print("❌ Error:", e)
        return f"Error: {e}"

# Step 6: Launch the interface
gr.Interface(
    fn=rag_query_ui,
    inputs="text",
    outputs="text",
    title="CEO Assistant - Burger Sales Q2",
    description="Ask questions like 'What were last quarter’s sales by region?'"
).launch()
