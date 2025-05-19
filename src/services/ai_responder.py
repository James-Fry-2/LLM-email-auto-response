import openai
import os
from dotenv import load_dotenv
from typing import Dict, Optional
from datetime import datetime
import json

load_dotenv()

class AIResponder:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4.1-mini"  

    def generate_response(self, customer_name: str, customer_info: str, email_body: str, request_type: Optional[str] = None) -> str:
        # Build a more comprehensive prompt with system context
        system_prompt = """You are an AI customer support agent for an appointment booking system. 
        Your role is to provide helpful, accurate, and personalized responses to customer inquiries.
        Always maintain a professional and friendly tone while being concise and clear."""

        # Add customer context
        customer_context = f"""
        Customer Name: {customer_name}
        Customer Information: {customer_info}
        """

        # Add request type context if available
        request_context = ""
        if request_type:
            request_context = f"\nRequest Type: {request_type}"

        # Combine all context
        prompt = f"{system_prompt}\n\n{customer_context}{request_context}\n\nCustomer's Message:\n{email_body}\n\nYour Response:"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{customer_context}{request_context}\n\nCustomer's Message:\n{email_body}"}
                ],
                temperature=0.7,
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"I apologize, but I'm having trouble generating a response at the moment. Please try again later. Error: {str(e)}"

    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze the sentiment of customer messages"""
        try:
            print(f"Analyzing sentiment for text: {text}")  # Debug log
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Analyze the sentiment of the following text and respond with ONLY one word: 'positive', 'negative', or 'neutral'."},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=10
            )
            sentiment = response.choices[0].message.content.strip().lower()
            print(f"Received sentiment: {sentiment}")  # Debug log
            return {
                "sentiment": sentiment,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")  # Debug log
            return {
                "sentiment": "neutral",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def extract_key_information(self, text: str) -> Dict:
        """Extract key information from customer messages"""
        try:
            print(f"Extracting information from text: {text}")  # Debug log
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Extract key information from the following text. Return a JSON object with these fields: name, phone, date, time, request_type. If a field is not found, use null."},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=200
            )
            response_text = response.choices[0].message.content.strip()
            print(f"Received response: {response_text}")  # Debug log
            extracted_info = json.loads(response_text)
            print(f"Parsed JSON: {extracted_info}")  # Debug log
            return {
                "extracted_info": extracted_info,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error in information extraction: {str(e)}")  # Debug log
            return {
                "extracted_info": {},
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def test_openai_connection(self) -> bool:
        """
        Test the connection to OpenAI API by making a simple completion request.
        Returns True if the connection is successful, False otherwise.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'test successful' if you can read this."}
                ],
                max_tokens=10
            )
            result = response.choices[0].message.content.strip()
            print(f"OpenAI connection test response: {result}")
            return True
        except Exception as e:
            print(f"OpenAI connection test failed: {str(e)}")
            return False 