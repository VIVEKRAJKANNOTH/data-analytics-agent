import os
import pandas as pd
from agent import AnalyticsAgent
from dotenv import load_dotenv

load_dotenv()

def test_agent():
    print("Initializing agent...")
    agent = AnalyticsAgent()
    
    # Create a dummy CSV
    csv_path = os.path.abspath("test_data.csv")
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    df.to_csv(csv_path, index=False)
    
    print(f"Loading dataset: {csv_path}")
    agent.load_dataset(csv_path)
    
    print("Sending chat message...")
    try:
        response = agent.chat("Calculate the sum of column A")
        print("Response received:")
        print(response)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")

if __name__ == "__main__":
    test_agent()
