import gradio as gr
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pandas as pd
import ollama
import torch # <-- NEW: Import torch to manage GPU device

# --- GPU SETUP: Check for CUDA and set device ---
if torch.cuda.is_available():
    EMBEDDING_DEVICE = 'cuda'
    print("PyTorch detected CUDA. Embeddings will run on NVIDIA GPU.")
else:
    EMBEDDING_DEVICE = 'cpu'
    print("CUDA not detected. Embeddings will run on CPU.")

# Step 1: Load Excel Data
df = pd.read_excel("retail_burger_sales.xlsx")

# Assume your Excel has columns: Date, Location, Total_Sales
summaries = df.apply(
    lambda row: f"On {row['Date']}, total burger sales in {row['Location']} were ${row['Total_Sales']}.",
    axis=1
).tolist()

# Step 2: Create embeddings
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# --- FIX 1: Force embedding creation onto the GPU ---
embeddings = embedder.encode(summaries, device=EMBEDDING_DEVICE)

# Step 3: Store in FAISS index
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# Step 4: Define query function
def generate_answer_with_llama3(query):
    # --- FIX 2: Force query encoding onto the GPU ---
    query_embedding = embedder.encode([query], device=EMBEDDING_DEVICE)
    
    _, I = index.search(query_embedding, k=3)
    context = "\n".join([summaries[i] for i in I[0]])

    prompt = f"""Answer the following query based on the burger sales data below.

Query: {query}

Context:
{context}

Answer:"""

    # Ollama handles its own GPU usage, which we assume is correct
    response = ollama.chat(
        model='llama3',
        messages=[
            {"role": "system", "content": "You are a helpful assistant for analyzing burger sales."},
            {"role": "user", "content": prompt}
        ]
    )

    return response['message']['content']

# Step 5: Gradio UI (rest of the code remains the same)
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
    description="Ask questions like 'Which branch had the highest sales last month?'"
).launch()