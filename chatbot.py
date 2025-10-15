import google.generativeai as genai
from config import GEMINI_API_KEY, SYSTEM_PROMPT, MAX_CONVERSATION_LENGTH
import time
from typing import List, Dict, Optional

class MentalHealthChatbot:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Create model WITHOUT system_instruction
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "max_output_tokens": 1024,
            }
        )
    
        # Include system prompt in the chat history instead
        self.chat_session = self.model.start_chat(
            history=[
                {
                    "role": "user", 
                    "parts": [SYSTEM_PROMPT]
                },
                {
                    "role": "model", 
                    "parts": ["I understand. I'm here to provide compassionate, empathetic mental health support. I'll be supportive and understanding, and mention professional help only when appropriate for severe distress or crisis situations."]
                }
            ]
        )
        self.conversation_history = []
        self.first_message = True  
        
    def get_response(self, user_message: str) -> str:
        try:
            from safety import validate_user_input, detect_crisis_keywords, get_crisis_response
            
            validation = validate_user_input(user_message)
            if not validation['is_valid']:
                return validation['message']
            
            if validation['is_crisis']:
                return get_crisis_response()
            
            self.conversation_history.append({"role": "user", "content": user_message})
            
            if len(self.conversation_history) > MAX_CONVERSATION_LENGTH:
                self.conversation_history = self.conversation_history[-MAX_CONVERSATION_LENGTH:]
            
            response = self.chat_session.send_message(user_message)
            bot_response = response.text
            
            if self.first_message:
                bot_response += "\n\n*I'm here to listen and support you. If you need more personalized help, check out our 1-to-1 professional support feature on the website.*"
                self.first_message = False
            elif self._contains_severe_distress(user_message):
                bot_response += "\n\n*It sounds like you're going through a really difficult time. You might benefit from our 1-to-1 professional help feature where you can connect with licensed mental health professionals.*"
            
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            
            return bot_response
            
        except Exception as e:
            return self._handle_error(e)
    
    def _contains_severe_distress(self, message: str) -> bool:
        severe_distress_keywords = [
            'can\'t cope', 'can\'t handle', 'overwhelming', 'falling apart',
            'breaking down', 'can\'t go on', 'losing control', 'spiraling',
            'severe depression', 'panic attacks', 'mental breakdown',
            'can\'t function', 'completely lost', 'desperate', 'trapped'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in severe_distress_keywords)
    
    def _handle_error(self, error) -> str:
        error_str = str(error).lower()
        
        if "quota" in error_str or "limit" in error_str:
            return ("I'm experiencing high traffic right now. Please try again in a few moments. "
                    "If you're in crisis, please contact a mental health professional or emergency services.")
        
        elif "api_key" in error_str:
            return ("I'm having technical difficulties. Please try again later. "
                    "If this is an emergency, please contact emergency services.")
        
        else:
            return ("I apologize, I'm having technical difficulties. Please try again in a moment. "
                    "If you need immediate support, please reach out to a mental health professional.")
    
    def reset_conversation(self):
        # Recreate chat with system prompt
        self.chat_session = self.model.start_chat(
            history=[
                {
                    "role": "user", 
                    "parts": [SYSTEM_PROMPT]
                },
                {
                    "role": "model", 
                    "parts": ["I understand. I'm here to provide compassionate mental health support."]
                }
            ]
        )
        self.conversation_history = []
        self.first_message = True 
    
    def get_conversation_history(self) -> List[Dict]:
        return self.conversation_history