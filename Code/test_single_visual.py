"""Quick test of visual query with llava:13b"""
from gradio_client import Client, handle_file
import os

# Connect to the running bot
client = Client("http://127.0.0.1:7860")

# Test image path
image_path = os.path.abspath("../images/sales_state_kpi_2024-06.png")
print(f"Testing with image: {image_path}")
print(f"Image exists: {os.path.exists(image_path)}")

# Test query
query = "Summarize the table in this image (key metrics + highlights)."
model = "llava:latest"

print(f"\n🧪 Testing visual query...")
print(f"Query: {query}")
print(f"Model: {model}")
print(f"Image: {os.path.basename(image_path)}")

try:
    result = client.predict(
        query,
        handle_file(image_path),
        model,
        api_name="/multimodal_query"
    )
    print(f"\n✅ Success!")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
except Exception as e:
    print(f"\n❌ Error: {e}")
