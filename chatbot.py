import google.generativeai as genai
from config import GEMINI_API_KEY, SYSTEM_PROMPT, MAX_CONVERSATION_LENGTH
from crisis_handler import CrisisHandler
from typing import List, Dict
from datetime import datetime
import json

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
                response = self.crisis_handler.get_immediate_crisis_response()
                # Store in history as well
                self.conversation_history.append({
                    "role": "user", 
                    "content": user_message,
                    "timestamp": datetime.now().isoformat()
                })
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": response,
                    "crisis_level": "immediate",
                    "timestamp": datetime.now().isoformat()
                })
                return response
                
            elif crisis_level == "high":
                response = self.crisis_handler.get_high_risk_response(user_message)
                # Store in history
                self.conversation_history.append({
                    "role": "user", 
                    "content": user_message,
                    "timestamp": datetime.now().isoformat()
                })
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": response,
                    "crisis_level": "high",
                    "timestamp": datetime.now().isoformat()
                })
                return response
            
            self.conversation_history.append({
                "role": "user", 
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            
            if len(self.conversation_history) > MAX_CONVERSATION_LENGTH:
                self.conversation_history = self.conversation_history[-MAX_CONVERSATION_LENGTH:]
            
            response = self.chat_session.send_message(user_message)
            bot_response = response.text
            
            # Add empathetic context based on message sentiment
            bot_response = self.crisis_handler.enhance_with_empathy(bot_response, user_message)
            
            # Add styled informational messages
            if self.first_message:
                first_msg_html = """
<div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 20px; border-radius: 12px; margin-top: 15px; box-shadow: 0 4px 15px rgba(168, 237, 234, 0.3);">
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <span style="font-size: 24px; margin-right: 10px;">💙</span>
        <p style="margin: 0; color: #2d3748; font-size: 15px; line-height: 1.6;">
            <strong>I'm here to listen and support you</strong> at your own pace. Take all the time you need.
        </p>
    </div>
    <div style="background: rgba(255, 255, 255, 0.6); border-radius: 8px; padding: 12px; margin-top: 10px;">
        <p style="margin: 0; color: #2d3748; font-size: 14px;">
            <strong>👨‍⚕️ Need personalized help?</strong> Our 1-to-1 professional support connects you with licensed mental health professionals.
        </p>
    </div>
</div>
"""
                bot_response += first_msg_html
                self.first_message = False
                
            elif crisis_level == "moderate":
                moderate_html = """
<div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); padding: 18px; border-radius: 12px; margin-top: 15px; box-shadow: 0 4px 15px rgba(255, 236, 210, 0.3);">
    <div style="display: flex; align-items: center;">
        <span style="font-size: 24px; margin-right: 12px;">🤗</span>
        <div>
            <p style="margin: 0 0 8px 0; color: #2d3748; font-size: 15px; font-weight: 600;">
                What you're sharing sounds really challenging
            </p>
            <p style="margin: 0; color: #2d3748; font-size: 14px; line-height: 1.5;">
                I'm here to support you. If things feel overwhelming, our <strong>professional support team is available 24/7</strong>.
            </p>
        </div>
    </div>
</div>
"""
                bot_response += moderate_html
            
            self.conversation_history.append({
                "role": "assistant", 
                "content": bot_response,
                "timestamp": datetime.now().isoformat()
            })
            
            return bot_response
            
        except Exception as e:
            return self._handle_error(e)
    
    def _handle_error(self, error) -> str:
        """Handle errors with styled HTML response"""
        error_str = str(error).lower()
        
        error_html_base = """
<div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(250, 112, 154, 0.3);">
    <div style="display: flex; align-items: center; margin-bottom: 15px;">
        <span style="font-size: 28px; margin-right: 12px;">⚠️</span>
        <h4 style="margin: 0; color: #2d3748; font-size: 18px; font-weight: 700;">{title}</h4>
    </div>
    <p style="color: #2d3748; font-size: 15px; line-height: 1.6; margin-bottom: 15px;">
        {message}
    </p>
    <div style="background: rgba(255, 255, 255, 0.6); border-radius: 8px; padding: 15px;">
        <p style="margin: 0 0 10px 0; color: #2d3748; font-size: 14px; font-weight: 600;">
            📞 If you need immediate support:
        </p>
        <div style="margin-left: 10px;">
            <p style="margin: 5px 0; color: #2d3748; font-size: 14px;">
                • <strong>988</strong> - Suicide & Crisis Lifeline (US)
            </p>
            <p style="margin: 5px 0; color: #2d3748; font-size: 14px;">
                • <strong>Text HOME to 741741</strong> - Crisis Text Line
            </p>
        </div>
    </div>
</div>
"""
        
        if "quota" in error_str or "limit" in error_str:
            return error_html_base.format(
                title="High Traffic - Please Retry",
                message="I'm experiencing high traffic right now, but I want to make sure you're okay. Please try again in a few moments."
            )
        
        elif "api_key" in error_str:
            return error_html_base.format(
                title="Technical Difficulties",
                message="I'm having technical difficulties, and I apologize. Please try again shortly."
            )
        
        else:
            return error_html_base.format(
                title="Connection Issue",
                message="I apologize, I'm having technical difficulties. Please try again in a moment."
            )
    
    def load_conversation_history(self, history: List[Dict]):
        """Load conversation history from storage"""
        self.conversation_history = history
        if len(history) > 0:
            self.first_message = False
            
            # Rebuild chat session with history
            chat_history = [
                {
                    "role": "user", 
                    "parts": [SYSTEM_PROMPT]
                },
                {
                    "role": "model", 
                    "parts": ["I understand. I'm here to provide compassionate mental health support."]
                }
            ]
            
            # Add previous messages to chat history
            for msg in history:
                if msg["role"] == "user":
                    chat_history.append({
                        "role": "user",
                        "parts": [msg["content"]]
                    })
                elif msg["role"] == "assistant":
                    chat_history.append({
                        "role": "model",
                        "parts": [msg["content"]]
                    })
            
            # Recreate chat session with full history
            self.chat_session = self.model.start_chat(history=chat_history)
    
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