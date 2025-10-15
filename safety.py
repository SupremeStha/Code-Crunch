import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

def configure_safety_settings():
    """Configure safety settings for mental health chatbot"""
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
    return safety_settings

def detect_crisis_keywords(message: str) -> bool:
    """Detect crisis-related keywords in user messages"""
    crisis_keywords = [
        'suicide', 'kill myself', 'end my life', 'want to die',
        'hurt myself', 'self harm', 'overdose', 'pills',
        'jump', 'bridge', 'gun', 'knife', 'cutting',
        'hopeless', 'worthless', 'better off dead'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in crisis_keywords)

def get_crisis_response() -> str:
    """Return appropriate crisis response"""
    return """I'm very concerned about what you're sharing. Your life has value and there are people who want to help.

🚨 **Immediate Help:**
- Call 988 (Suicide & Crisis Lifeline) - Available 24/7
- Text HOME to 741741 (Crisis Text Line)
- Go to your nearest emergency room
- Call 911

🤗 **You're not alone:** These feelings can be overwhelming, but they can change. 

💬 **Get personalized support:** Our website also offers 1-to-1 professional help where you can connect directly with licensed therapists and counselors.

Would you like to talk about what's making you feel this way? I'm here to listen, but please also reach out to the crisis resources above for immediate support."""

def moderate_response(response: str, user_message: str) -> str:
    """Moderate bot response for safety - only add disclaimers when necessary"""
    if detect_crisis_keywords(user_message):
        return get_crisis_response()
    
    return response

def contains_inappropriate_content(message: str) -> bool:
    """Check for inappropriate content"""
    inappropriate_keywords = [
        'violence', 'illegal', 'drugs', 'weapons'
    ]
    
    return any(keyword in message.lower() for keyword in inappropriate_keywords)

def validate_user_input(message: str) -> dict:
    """Validate and categorize user input"""
    result = {
        'is_valid': True,
        'is_crisis': False,
        'is_inappropriate': False,
        'message': ''
    }
    
    if not message or len(message.strip()) == 0:
        result['is_valid'] = False
        result['message'] = "Please enter a message."
        return result
    
    if len(message) > 1000:
        result['is_valid'] = False
        result['message'] = "Please keep your message under 1000 characters."
        return result
    
    if detect_crisis_keywords(message):
        result['is_crisis'] = True
    
    if contains_inappropriate_content(message):
        result['is_inappropriate'] = True
        result['message'] = "I can't respond to that type of content. Let's focus on your mental health and wellbeing."
    
    return result