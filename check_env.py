from dotenv import load_dotenv
import os

load_dotenv()

key = os.getenv("GOOGLE_API_KEY")
if key:
    print(f"GOOGLE_API_KEY found: {key[:5]}...")
else:
    print("GOOGLE_API_KEY not found in environment")

# List all keys to see if it's named differently
print("Available keys:", [k for k in os.environ.keys() if 'API' in k or 'GOOGLE' in k])
