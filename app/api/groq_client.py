import httpx
from typing import List, Dict, Any, Optional
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "qwen-qwq-32b"
        logger.info(f"Initialized GroqClient with model: {self.model}")
        
    def generate_response(self, message: str, context: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Generate a response using the Groq API with Qwen-32B model
        
        Args:
            message: The user's message
            context: Optional list of previous interactions for context
            
        Returns:
            The generated response text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare system message with instructions
        system_message = """
        You are an AI Business Assistant that helps with customer inquiries, 
        scheduling meetings, and providing information. Be professional, 
        helpful, and concise in your responses.
        """
        
        # Prepare messages including context from memory if available
        messages = [{"role": "system", "content": system_message}]
        
        # Add context from memory if available
        if context:
            logger.info(f"Adding {len(context)} context items from memory")
            for item in context:
                messages.append({"role": "user", "content": item.get("query", "")})
                messages.append({"role": "assistant", "content": item.get("response", "")})
        
        # Add the current message
        messages.append({"role": "user", "content": message})
        
        try:
            logger.info("Sending request to Groq API")
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 1024
                    }
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    logger.info("Successfully received response from Groq API")
                    return response_data["choices"][0]["message"]["content"]
                else:
                    error_message = f"Error from Groq API: {response.status_code} - {response.text}"
                    logger.error(error_message)
                    return f"I'm sorry, I encountered an error: {error_message}"
                    
        except Exception as e:
            error_msg = f"Exception when calling Groq API: {str(e)}"
            logger.error(error_msg)
            return "I'm sorry, I encountered an error while processing your request."