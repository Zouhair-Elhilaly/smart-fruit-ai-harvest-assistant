import requests
import os   
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

api = os.getenv("HUGGINGFACE_API_KEY")  # Get the Hugging Face API key from environment variables

from huggingface_hub import InferenceClient

# Initialize the client with your token
client = InferenceClient(token=api)

# Pass the image path and specify the model
caption = client.image_to_text(
    "./assets/overripe.jpg", 
    model="nlpconnect/vit-gpt2-image-captioning"
)

print(caption.generated_text)