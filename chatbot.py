import google.generativeai as genai
from config import GEMINI_API_KEY, SYSTEM_PROMPT, MAX_CONVERSATION_LENGTH
from crisis_handler import CrisisHandler
from typing import List, Dict, Optional
from datetime import datetime, date, time
import json
import re

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
        
        # Booking state management
        self.booking_state = {
            "active": False,
            "step": None,
            "data": {}
        }
        
    def detect_booking_intent(self, user_message: str) -> bool:
        """Detect if user wants to book an appointment"""
        booking_keywords = [
            "book", "appointment", "schedule", "meet", "session",
            "talk to professional", "see a therapist", "consultation",
            "need help from professional", "therapist", "counselor"
        ]
        
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in booking_keywords)
    
    def extract_booking_info(self, user_message: str, current_step: str) -> Optional[str]:
        """Extract relevant information based on booking step"""
        message = user_message.strip()
        
        if current_step == "name":
            # Basic name validation (2+ chars, letters and spaces)
            if len(message) >= 2 and re.match(r'^[a-zA-Z\s]+$', message):
                return message
                
        elif current_step == "email":
            # Email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(email_pattern, message):
                return message
                
        elif current_step == "phone":
            # Phone validation (digits, spaces, +, -, ())
            phone_clean = re.sub(r'[\s\-\(\)]', '', message)
            if re.match(r'^\+?[\d]{7,15}$', phone_clean):
                return message
                
        elif current_step == "service":
            # Service type selection
            services = {
                "1": "Consultation",
                "2": "Follow-up Session",
                "3": "Therapy Session",
                "4": "Mental Health Assessment",
                "5": "Other"
            }
            
            # Check if it's a number selection
            if message in services:
                return services[message]
            
            # Check if they typed the service name
            message_lower = message.lower()
            for key, value in services.items():
                if value.lower() in message_lower:
                    return value
                    
        elif current_step == "date":
            # Date validation (YYYY-MM-DD or common formats)
            try:
                # Try parsing different date formats
                for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        parsed_date = datetime.strptime(message, fmt).date()
                        # Check if date is in the future
                        if parsed_date >= date.today():
                            return parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            except:
                pass
                
        elif current_step == "time":
            # Time validation (HH:MM format)
            try:
                for fmt in ['%H:%M', '%I:%M %p', '%I:%M%p']:
                    try:
                        parsed_time = datetime.strptime(message, fmt).time()
                        return parsed_time.strftime('%H:%M')
                    except ValueError:
                        continue
            except:
                pass
        
        return None
    
    def start_booking_flow(self) -> str:
        """Initialize the booking process"""
        self.booking_state = {
            "active": True,
            "step": "professional_list",
            "data": {}
        }
        
        # Return a message that tells the frontend to fetch and display professionals
        return """
<div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 20px; border-radius: 12px; margin-top: 15px; box-shadow: 0 4px 15px rgba(168, 237, 234, 0.3);">
    <div style="display: flex; align-items: center; margin-bottom: 15px;">
        <span style="font-size: 28px; margin-right: 12px;">📅</span>
        <h3 style="margin: 0; color: #2d3748; font-size: 18px; font-weight: 700;">Book an Appointment</h3>
    </div>
    <p style="margin: 0 0 15px 0; color: #2d3748; font-size: 15px; line-height: 1.6;">
        Great! I'll help you book an appointment with one of our mental health professionals.
    </p>
    <div style="background: rgba(255, 255, 255, 0.6); border-radius: 8px; padding: 15px; margin-bottom: 15px;">
        <p style="margin: 0; color: #2d3748; font-size: 14px; font-weight: 600;">
            📋 Information needed: Name, Email, Phone, Service Type, Preferred Date & Time
        </p>
    </div>
    <p style="margin: 0; color: #2d3748; font-size: 14px; font-style: italic;">
        Loading our available professionals...
    </p>
</div>
<div data-load-professionals="true"></div>
"""
    
    def handle_booking_flow(self, user_message: str) -> tuple[str, bool]:
        """Handle the booking conversation flow
        Returns: (response_message, is_booking_complete)
        """
        current_step = self.booking_state["step"]
        
        # Professional selection - waiting for list to load
        if current_step == "professional_list":
            # Check if user is trying to select a professional
            match = re.search(r'professional\s+id\s+(\d+)', user_message.lower())
            if match:
                # User clicked a card, process the selection
                prof_id = int(match.group(1))
                self.booking_state["data"]["professional_id"] = prof_id
                self.booking_state["step"] = "name"
                
                return """
<div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; border-radius: 8px; margin-top: 15px;">
    <p style="margin: 0; color: #155724; font-size: 15px;">✅ Professional selected!</p>
</div>

<div style="background: white; border-radius: 12px; padding: 20px; margin-top: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <p style="margin: 0 0 10px 0; color: #2d3748; font-size: 15px; font-weight: 600;">📝 Step 1 of 6: What's your full name?</p>
    <p style="margin: 0; color: #666; font-size: 13px;">Please enter your full name as you'd like it to appear on the appointment.</p>
</div>
""", False
            else:
                # Still waiting for selection
                return "Please select a professional from the list above by clicking on their card.", False
            
        # Professional selection (legacy - shouldn't reach here anymore)
        elif current_step == "professional":
            # Extract professional ID from message
            match = re.search(r'professional\s+id\s+(\d+)', user_message.lower())
            if match:
                prof_id = int(match.group(1))
                self.booking_state["data"]["professional_id"] = prof_id
                self.booking_state["step"] = "name"
                
                return """
<div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; border-radius: 8px; margin-top: 15px;">
    <p style="margin: 0; color: #155724; font-size: 15px;">✅ Professional selected!</p>
</div>

<div style="background: white; border-radius: 12px; padding: 20px; margin-top: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <p style="margin: 0 0 10px 0; color: #2d3748; font-size: 15px; font-weight: 600;">📝 Step 1 of 6: What's your full name?</p>
    <p style="margin: 0; color: #666; font-size: 13px;">Please enter your full name as you'd like it to appear on the appointment.</p>
</div>
""", False
            else:
                return "Please select a professional from the list above by clicking on their card.", False
        
        # Name
        elif current_step == "name":
            extracted = self.extract_booking_info(user_message, "name")
            if extracted:
                self.booking_state["data"]["name"] = extracted
                self.booking_state["step"] = "email"
                return f"""
<div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; border-radius: 8px; margin-top: 15px;">
    <p style="margin: 0; color: #155724; font-size: 15px;">✅ Thanks, {extracted}!</p>
</div>

<div style="background: white; border-radius: 12px; padding: 20px; margin-top: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <p style="margin: 0 0 10px 0; color: #2d3748; font-size: 15px; font-weight: 600;">📧 Step 2 of 6: What's your email address?</p>
    <p style="margin: 0; color: #666; font-size: 13px;">We'll send appointment confirmation and reminders to this email.</p>
</div>
""", False
            else:
                return "Please enter a valid name (letters and spaces only, at least 2 characters).", False
        
        # Email
        elif current_step == "email":
            extracted = self.extract_booking_info(user_message, "email")
            if extracted:
                self.booking_state["data"]["email"] = extracted
                self.booking_state["step"] = "phone"
                return """
<div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; border-radius: 8px; margin-top: 15px;">
    <p style="margin: 0; color: #155724; font-size: 15px;">✅ Email saved!</p>
</div>

<div style="background: white; border-radius: 12px; padding: 20px; margin-top: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <p style="margin: 0 0 10px 0; color: #2d3748; font-size: 15px; font-weight: 600;">📱 Step 3 of 6: What's your phone number?</p>
    <p style="margin: 0; color: #666; font-size: 13px;">Include country code if international (e.g., +1 555-123-4567)</p>
</div>
""", False
            else:
                return "Please enter a valid email address (e.g., name@example.com).", False
        
        # Phone
        elif current_step == "phone":
            extracted = self.extract_booking_info(user_message, "phone")
            if extracted:
                self.booking_state["data"]["phone"] = extracted
                self.booking_state["step"] = "service"
                return """
<div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; border-radius: 8px; margin-top: 15px;">
    <p style="margin: 0; color: #155724; font-size: 15px;">✅ Phone number saved!</p>
</div>

<div style="background: white; border-radius: 12px; padding: 20px; margin-top: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <p style="margin: 0 0 15px 0; color: #2d3748; font-size: 15px; font-weight: 600;">🏥 Step 4 of 6: What type of service do you need?</p>
    <div style="background: #f8f9fa; border-radius: 8px; padding: 15px;">
        <p style="margin: 0 0 10px 0; color: #2d3748; font-weight: 600;">Please type the number or name:</p>
        <ol style="margin: 0; padding-left: 20px; color: #2d3748; line-height: 2;">
            <li><strong>Consultation</strong> - Initial meeting</li>
            <li><strong>Follow-up Session</strong> - Continuing treatment</li>
            <li><strong>Therapy Session</strong> - Regular therapy</li>
            <li><strong>Mental Health Assessment</strong> - Evaluation</li>
            <li><strong>Other</strong> - Something else</li>
        </ol>
    </div>
</div>
""", False
            else:
                return "Please enter a valid phone number (7-15 digits, may include +, -, spaces, or parentheses).", False
        
        # Service
        elif current_step == "service":
            extracted = self.extract_booking_info(user_message, "service")
            if extracted:
                self.booking_state["data"]["service"] = extracted
                self.booking_state["step"] = "date"
                return f"""
<div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; border-radius: 8px; margin-top: 15px;">
    <p style="margin: 0; color: #155724; font-size: 15px;">✅ Service selected: {extracted}</p>
</div>

<div style="background: white; border-radius: 12px; padding: 20px; margin-top: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <p style="margin: 0 0 10px 0; color: #2d3748; font-size: 15px; font-weight: 600;">📅 Step 5 of 6: What's your preferred date?</p>
    <p style="margin: 0; color: #666; font-size: 13px;">Enter date in format: YYYY-MM-DD (e.g., 2025-12-25) or DD/MM/YYYY</p>
    <p style="margin: 5px 0 0 0; color: #666; font-size: 12px;"><em>Note: Date must be today or in the future</em></p>
</div>
""", False
            else:
                return "Please enter a valid service number (1-5) or type the service name.", False
        
        # Date
        elif current_step == "date":
            extracted = self.extract_booking_info(user_message, "date")
            if extracted:
                self.booking_state["data"]["date"] = extracted
                self.booking_state["step"] = "time"
                return f"""
<div style="background: #d4edda; border-left: 4px solid #28a745; padding: 15px; border-radius: 8px; margin-top: 15px;">
    <p style="margin: 0; color: #155724; font-size: 15px;">✅ Date set: {extracted}</p>
</div>

<div style="background: white; border-radius: 12px; padding: 20px; margin-top: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <p style="margin: 0 0 10px 0; color: #2d3748; font-size: 15px; font-weight: 600;">🕐 Step 6 of 6: What time works best for you?</p>
    <p style="margin: 0; color: #666; font-size: 13px;">Enter time in 24-hour format (e.g., 14:30) or 12-hour format (e.g., 2:30 PM)</p>
</div>
""", False
            else:
                return "Please enter a valid future date in format YYYY-MM-DD, DD/MM/YYYY, or MM/DD/YYYY.", False
        
        # Time - Final step
        elif current_step == "time":
            extracted = self.extract_booking_info(user_message, "time")
            if extracted:
                self.booking_state["data"]["time"] = extracted
                self.booking_state["step"] = "confirm"
                
                # Format confirmation message
                booking_data = self.booking_state["data"]
                return f"""
<div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); border-left: 4px solid #28a745; padding: 20px; border-radius: 12px; margin-top: 15px; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.2);">
    <h3 style="margin: 0 0 15px 0; color: #155724; font-size: 18px; font-weight: 700;">✅ Booking Summary</h3>
    <div style="background: white; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 10px 0; color: #666; font-weight: 600;">Name:</td>
                <td style="padding: 10px 0; color: #2d3748;">{booking_data['name']}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 10px 0; color: #666; font-weight: 600;">Email:</td>
                <td style="padding: 10px 0; color: #2d3748;">{booking_data['email']}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 10px 0; color: #666; font-weight: 600;">Phone:</td>
                <td style="padding: 10px 0; color: #2d3748;">{booking_data['phone']}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 10px 0; color: #666; font-weight: 600;">Service:</td>
                <td style="padding: 10px 0; color: #2d3748;">{booking_data['service']}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 10px 0; color: #666; font-weight: 600;">Date:</td>
                <td style="padding: 10px 0; color: #2d3748;">{booking_data['date']}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; color: #666; font-weight: 600;">Time:</td>
                <td style="padding: 10px 0; color: #2d3748;">{booking_data['time']}</td>
            </tr>
        </table>
    </div>
    <p style="margin: 15px 0 0 0; color: #155724; font-size: 14px; font-weight: 600;">
        Type "confirm" to complete your booking, or "cancel" to start over.
    </p>
</div>
""", False
            else:
                return "Please enter a valid time in format HH:MM (24-hour) or HH:MM AM/PM (12-hour).", False
        
        # Confirmation
        elif current_step == "confirm":
            message_lower = user_message.lower().strip()
            if message_lower in ["confirm", "yes", "book", "book it"]:
                # Mark as complete and return empty string
                # The actual booking will be handled by the frontend calling /chat/complete-booking
                self.booking_state["step"] = "completed"
                return "", True
            elif message_lower in ["cancel", "no", "restart"]:
                self.booking_state = {"active": False, "step": None, "data": {}}
                return """
<div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 8px; margin-top: 15px;">
    <p style="margin: 0; color: #856404; font-size: 15px;">❌ Booking cancelled. Let me know if you'd like to start over!</p>
</div>
""", False
            else:
                return "Please type 'confirm' to complete the booking or 'cancel' to start over.", False
        
        return "Something went wrong. Please type 'book appointment' to start over.", False
    
    def get_booking_data(self) -> dict:
        """Return the collected booking data"""
        return self.booking_state.get("data", {})
    
    def reset_booking(self):
        """Reset booking state"""
        self.booking_state = {"active": False, "step": None, "data": {}}
        
    def get_response(self, user_message: str) -> str:
        try:
            from safety import validate_user_input
            
            validation = validate_user_input(user_message)
            if not validation['is_valid']:
                return validation['message']
            
            # Check if booking is active
            if self.booking_state["active"]:
                response, is_complete = self.handle_booking_flow(user_message)
                
                # Store in history
                self.conversation_history.append({
                    "role": "user", 
                    "content": user_message,
                    "timestamp": datetime.now().isoformat()
                })
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": response,
                    "booking_complete": is_complete,
                    "timestamp": datetime.now().isoformat()
                })
                
                return response
            
            # Check if user wants to book
            if self.detect_booking_intent(user_message):
                response = self.start_booking_flow()
                
                # Store in history
                self.conversation_history.append({
                    "role": "user", 
                    "content": user_message,
                    "timestamp": datetime.now().isoformat()
                })
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                })
                
                return response
            
            # Enhanced crisis detection
            crisis_level = self.crisis_handler.detect_crisis_level(user_message)
            
            if crisis_level == "immediate":
                response = self.crisis_handler.get_immediate_crisis_response()
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
            <strong>👨‍⚕️ Need personalized help?</strong> Just say <strong>"book appointment"</strong> and I'll help you schedule a session with one of our professionals.
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
                I'm here to support you. If things feel overwhelming, our <strong>professional support team is available 24/7</strong>. Just say "book appointment".
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
        self.reset_booking()
    
    def get_conversation_history(self) -> List[Dict]:
        return self.conversation_history
    
    def get_crisis_alert_count(self) -> int:
        """Return number of crisis incidents detected in current session"""
        return self.crisis_handler.crisis_detected_count