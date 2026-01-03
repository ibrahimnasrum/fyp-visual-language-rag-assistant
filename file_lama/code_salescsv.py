import gradio as gr
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pandas as pd
import ollama

# Step 1: Load CSV Data
# Make sure your CSV has columns: Date, Location, Total_Sales
df = pd.read_csv("retail_burger_sales.csv")

# Step 2: Create readable summaries from your data
summaries = df.apply(
    lambda row: f"On {row['Date']}, total burger sales in {row['Region']} for {row['Product']} were ${row['Total Sale']}. "
                f"The employee in charge was {row['Employee']} and they sold {row['Quantity']} units at ${row['Unit Price']} each.",
    axis=1
).tolist()

# Step 3: Create embeddings
embedder = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = embedder.encode(summaries)

# Step 4: Store in FAISS index
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# Step 5: Define query function
def generate_answer_with_llama3(query):
    query_embedding = embedder.encode([query])
    _, I = index.search(query_embedding, k=3)
    context = "\n".join([summaries[i] for i in I[0]])

    prompt = f"""Answer the following query based on the burger sales data below.

Query: {query}

Context:
{context}

Answer:"""

    response = ollama.chat(
        model='llama3',
        messages=[
            {"role": "system", "content": "You are a helpful assistant for analyzing burger sales."},
            {"role": "user", "content": prompt}
        ]
    )

    return response['message']['content']

# Step 6: Gradio UI
def rag_query_ui(user_input):
    try:
        return generate_answer_with_llama3(user_input)
    except Exception as e:
        return f"Error: {e}"

gr.Interface(
    fn=rag_query_ui,
    inputs="text",
    outputs="text",
    title="Burger Sales Q&A Assistant",
    description="Ask questions like 'Which region had the highest sales last month?' or 'How many burgers did KL sell in May 2024?'"
).launch()
