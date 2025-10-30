import google.generativeai as genai
from config import GEMINI_API_KEY, SYSTEM_PROMPT, MAX_CONVERSATION_LENGTH
from crisis_handler import CrisisHandler
from typing import List, Dict

class MentalHealthChatbot:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "max_output_tokens": 1024,
            }
        )
    
        self.chat_session = self.model.start_chat(
            history=[
                {
                    "role": "user", 
                    "parts": [SYSTEM_PROMPT]
                },
                {
                    "role": "model", 
                    "parts": ["I understand. I'm here to provide compassionate, empathetic mental health support. I'll listen without judgment and validate your feelings."]
                }
            ]
        )
        self.conversation_history = []
        self.first_message = True
        self.crisis_handler = CrisisHandler()
        
    def get_response(self, user_message: str) -> str:
        try:
            from safety import validate_user_input
            
            validation = validate_user_input(user_message)
            if not validation['is_valid']:
                return validation['message']
            
            # Enhanced crisis detection
            crisis_level = self.crisis_handler.detect_crisis_level(user_message)
            
            if crisis_level == "immediate":
                return self.crisis_handler.get_immediate_crisis_response()
            elif crisis_level == "high":
                return self.crisis_handler.get_high_risk_response(user_message)
            
            self.conversation_history.append({"role": "user", "content": user_message})
            
            if len(self.conversation_history) > MAX_CONVERSATION_LENGTH:
                self.conversation_history = self.conversation_history[-MAX_CONVERSATION_LENGTH:]
            
            response = self.chat_session.send_message(user_message)
            bot_response = response.text
            
            # Add empathetic context based on message sentiment
            bot_response = self.crisis_handler.enhance_with_empathy(bot_response, user_message)
            
            if self.first_message:
                bot_response += "\n\n*I'm here to listen and support you at your own pace. If you need more personalized help, our 1-to-1 professional support feature connects you with licensed mental health professionals.*"
                self.first_message = False
            elif crisis_level == "moderate":
                bot_response += "\n\n*What you're sharing sounds really challenging. I'm here to support you. If things feel overwhelming, our professional support team is available 24/7.*"
            
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            
            return bot_response
            
        except Exception as e:
            return self._handle_error(e)
    
    def _handle_error(self, error) -> str:
        error_str = str(error).lower()
        
        if "quota" in error_str or "limit" in error_str:
            return (
                "I'm experiencing high traffic right now, but I want to make sure you're okay. "
                "Please try again in a few moments. If you're in distress, please contact:\n"
                "• **988**: Suicide & Crisis Lifeline (US)\n"
                "• **Crisis Text Line**: Text HOME to 741741"
            )
        
        elif "api_key" in error_str:
            return (
                "I'm having technical difficulties, and I apologize. "
                "If you need immediate support, please reach out to:\n"
                "• **988**: Suicide & Crisis Lifeline (US)\n"
                "• **Crisis Text Line**: Text HOME to 741741"
            )
        
        else:
            return (
                "I apologize, I'm having technical difficulties. Please try again in a moment. "
                "If you need immediate support, please contact:\n"
                "• **988**: Suicide & Crisis Lifeline (US)\n"
                "• **Crisis Text Line**: Text HOME to 741741"
            )
    
    def reset_conversation(self):
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
        self.crisis_handler.reset()
    
    def get_conversation_history(self) -> List[Dict]:
        return self.conversation_history
    
    def get_crisis_alert_count(self) -> int:
        """Return number of crisis incidents detected in current session"""
        return self.crisis_handler.crisis_detected_count