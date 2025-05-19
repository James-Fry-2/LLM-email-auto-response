import sys
import os

# Adjust path to find the 'src' directory from 'connection_tests' folder
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_script_dir)
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from services.ai_responder import AIResponder # Assuming this is where OpenAI client is
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Attempted to add {src_path} to sys.path based on script location.")
    print("Please ensure 'src' directory and required modules exist.")
    sys.exit(1)

def main():
    print("Attempting to test OpenAI connection...")
    
    # Load environment variables from .env file (especially OPENAI_API_KEY)
    load_dotenv(os.path.join(project_root, '.env')) # Load .env from project root
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables.")
        print("Please ensure it is set in your .env file in the project root.")
        return

    print(f"Found OPENAI_API_KEY starting with: {api_key[:5]}...")

    try:
        print("Initializing AIResponder...")
        ai_responder = AIResponder() # This should initialize the OpenAI client
        print("AIResponder initialized.")
        
        # You could add a simple test call here, e.g., a simple completion or model listing
        # For now, we'll just check if the client initialization in AIResponder works.
        # Example (requires ai_responder to have a method to test connection, or you make a direct client call):
        
        # Test with a simple prompt (optional, can be expanded)
        print("Testing AI response generation with a simple prompt...")
        test_prompt = "Hello OpenAI, this is a test!"
        # Assuming ai_responder has a generic method or you adapt it
        # For now, using analyze_sentiment as a proxy if it makes a call
        response = ai_responder.analyze_sentiment(test_prompt)
        print(f"Received response from analyze_sentiment: {response}")
        print("OpenAI connection test completed (based on AIResponder initialization and a test call). Check output for errors.")

    except Exception as e:
        print(f"\n--- ERROR DURING OPENAI CONNECTION TEST ---")
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 