import re
from typing import Dict, Optional

class CrisisHandler:
    """Handles crisis detection, response, and empathy enhancement"""
    
    def __init__(self):
        self.crisis_detected_count = 0
        self._init_keywords()
    
    def _init_keywords(self):
        """Initialize all crisis detection keywords and patterns"""
        # Immediate crisis indicators
        self.immediate_keywords = [
            r'\bharm\b.*\bself\b|\bself.*\bharm\b',
            r'\bsuicide\b|\bkill\s*myself\b|\bend\s*my\s*life\b',
            r'\bwant\s*to\s*die\b|\bwish\s*i\s*was\s*dead\b',
            r'\bplan.*suicide\b|\bmethod.*suicide\b',
            r'\bhurt\s*myself\b|\bcut\s*myself\b',
            r'\boverdose\b|\btake\s*pills\b',
            r'\bharm\s*others\b|\bhurt\s*someone\b',
            r'\babuse\b.*\bchild\b|\bchild.*\babuse\b',
        ]
        
        # High risk indicators
        self.high_risk_keywords = [
            r'\bno.*hope\b|\bhopeless\b',
            r'\bcan\'t.*cope\b|\bcan\'t\s*handle\b',
            r'\btrap.*\b|\btrapped\b',
            r'\bbreaking\s*down\b|\bmental\s*breakdown\b',
            r'\bspiraling\b|\bfalling\s*apart\b',
            r'\bnothing\s*matters\b|\bno\s*point\b',
            r'\bno\s*one\s*cares\b|\bcompletely\s*alone\b',
            r'\bdesperate\b|\bcan\'t\s*go\s*on\b',
        ]
        
        # Moderate distress keywords
        self.moderate_keywords = [
            'overwhelming', 'can\'t sleep', 'can\'t eat', 'anxious', 'panic',
            'depressed', 'worthless', 'failing', 'struggling', 'exhausted',
            'can\'t focus', 'numb', 'empty', 'hurt', 'pain', 'lonely'
        ]
        
        # Empathy context mapping
        self.empathy_prefixes = {
            r'\blonely\b|\balon[e]?\b': "I hear that you're feeling isolated. ",
            r'\bfailed\b|\bfailure\b': "It's understandable to feel discouraged. ",
            r'\bstuck\b|\btrapped\b': "Feeling stuck is genuinely difficult. ",
            r'\bsad\b|\bdepressed\b': "That sadness you're describing sounds really heavy. ",
            r'\bscared\b|\bfrightened\b|\banxious\b': "It makes sense that you're feeling anxious. ",
            r'\bannoyed\b|\bfrustrated\b|\bangry\b': "Your frustration is completely valid. ",
        }
    
    def detect_crisis_level(self, message: str) -> str:
        """
        Detect crisis level with three severity tiers:
        - immediate: Active harm/suicide/severe crisis
        - high: Strong distress indicators
        - moderate: Notable emotional difficulty
        - none: Normal conversation
        """
        message_lower = message.lower()
        
        # Check immediate crisis
        for pattern in self.immediate_keywords:
            if re.search(pattern, message_lower):
                self.crisis_detected_count += 1
                return "immediate"
        
        # Check high risk (2+ indicators)
        high_risk_count = sum(
            1 for pattern in self.high_risk_keywords 
            if re.search(pattern, message_lower)
        )
        if high_risk_count >= 2:
            self.crisis_detected_count += 1
            return "high"
        
        # Check moderate distress
        if any(keyword in message_lower for keyword in self.moderate_keywords):
            return "moderate"
        
        return "none"
    
    def get_immediate_crisis_response(self) -> str:
        """Response for immediate crisis situations"""
        return (
            "🚨 I'm genuinely concerned about what you've shared. Your safety is the priority.\n\n"
            "Please reach out for immediate support:\n"
            "• **National Suicide Prevention Lifeline**: 988 (call/text, US)\n"
            "• **Crisis Text Line**: Text HOME to 741741\n"
            "• **International Association for Suicide Prevention**: https://www.iasp.info/resources/Crisis_Centres/\n"
            "• **Emergency Services**: 911 (US) or your local emergency number\n\n"
            "You deserve support through this. Please contact one of these resources right now—they have people trained to help, "
            "and you won't be judged. If you're unable to reach these services, please go to your nearest emergency room.\n\n"
            "*I'm here, and I care about your wellbeing.*"
        )
    
    def get_high_risk_response(self, user_message: str) -> str:
        """Response for high-risk situations"""
        return (
            "I hear you, and I want you to know that what you're feeling is real and valid. "
            "The intensity of what you're experiencing right now is significant, and you shouldn't have to navigate this alone.\n\n"
            "**Please consider reaching out for professional support:**\n"
            "• **National Suicide Prevention Lifeline**: 988 (call/text, US)\n"
            "• **Crisis Text Line**: Text HOME to 741741\n"
            "• **Our 1-to-1 Professional Support**: Connect with a licensed mental health professional who can provide personalized care\n\n"
            "In the meantime, I'm here to listen. Can you tell me a bit more about what's happening right now? "
            "Sometimes talking through it can help, even in small steps.\n\n"
            "*You matter, and things can get better.*"
        )
    
    def enhance_with_empathy(self, response: str, user_message: str) -> str:
        """Add personalized empathetic touches based on user's emotional context"""
        message_lower = user_message.lower()
        
        for pattern, prefix in self.empathy_prefixes.items():
            if re.search(pattern, message_lower):
                return prefix + response
        
        return response
    
    def reset(self):
        """Reset crisis counter for new session"""
        self.crisis_detected_count = 0