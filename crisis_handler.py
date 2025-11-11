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
            # Self-harm patterns
            r'\bharm\b.*\bself\b|\bself.*\bharm\b',
            r'\bharm\s*myself\b|\bcut\s*myself\b',
            r'\bcausing\s+harm\b|\bwant.*harm\b|\bthinking.*harm\b',
            r'\binjure\s+myself\b|\binjuring\s+myself\b',
            
            # Suicide patterns
            r'\bsuicide\b|\bkill\s*myself\b|\bend\s*my\s*life\b',
            r'\bwant\s*to\s*die\b|\bwish\s*i\s*was\s*dead\b|\bbetter\s*off\s*dead\b',
            r'\bplan.*suicide\b|\bmethod.*suicide\b',
            r'\boverdose\b|\btake\s*pills\b|\btaking\s*pills\b',
            r'\bjump\s+off\b|\bhanging\b|\bhang\s+myself\b',
            
            # Additional self-harm
            r'\bhurt\s*myself\b|\bburning\s+myself\b',
            r'\bpunish\s+myself\b|\bdeserve\s+pain\b',
            
            # Harm to others
            r'\bharm\s*others\b|\bhurt\s*someone\b|\bhurt\s*people\b',
            r'\bkill\s+someone\b|\bviolent\s+thoughts\b',
            
            # Child safety
            r'\babuse\b.*\bchild\b|\bchild.*\babuse\b',
            r'\bharm.*\bchild\b|\bchild.*\bharm\b',
            
            # Immediate danger phrases
            r'\bcan\'t\s+take\s+it\b|\bcan\'t\s+do\s+this\b',
            r'\bending\s+it\s+all\b|\bgiving\s+up\b',
        ]
        
        # High risk indicators
        self.high_risk_keywords = [
            r'\bno.*hope\b|\bhopeless\b|\bno\s+way\s+out\b',
            r'\bcan\'t.*cope\b|\bcan\'t\s*handle\b|\bcan\'t\s+bear\b',
            r'\btrap.*\b|\btrapped\b|\bstuck\s+forever\b',
            r'\bbreaking\s*down\b|\bmental\s*breakdown\b|\blosing\s+it\b',
            r'\bspiraling\b|\bfalling\s*apart\b|\bfalling\s+apart\b',
            r'\bnothing\s*matters\b|\bno\s*point\b|\bpointless\b',
            r'\bno\s*one\s*cares\b|\bcompletely\s*alone\b|\bnobody\s+cares\b',
            r'\bdesperate\b|\bcan\'t\s*go\s*on\b|\bcan\'t\s+continue\b',
            r'\bbetter\s+off\s+without\s+me\b|\bburden\s+to\s+everyone\b',
            r'\bgive\s+up\b|\bgave\s+up\b|\bgiving\s+up\b',
        ]
        
        # Moderate distress keywords
        self.moderate_keywords = [
            'overwhelming', 'overwhelmed', "can't sleep", "can't eat", 'anxious', 'panic',
            'depressed', 'worthless', 'failing', 'struggling', 'exhausted',
            "can't focus", 'numb', 'empty', 'hurt', 'pain', 'lonely', 'scared',
            'terrified', 'breaking down', 'falling apart', 'drowning', 'suffocating'
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
        """Response for immediate crisis situations with HTML formatting"""
        return """
<div style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); padding: 25px; border-radius: 15px; color: white; box-shadow: 0 8px 20px rgba(231, 76, 60, 0.3); margin: 10px 0;">
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <span style="font-size: 32px; margin-right: 15px;">🆘</span>
        <h3 style="margin: 0; font-size: 22px; font-weight: 700;">I'm genuinely concerned about you</h3>
    </div>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
        Your safety is the absolute priority right now. Please reach out for immediate support—trained professionals are available and they truly care.
    </p>
    
    <div style="background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(10px); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
        <h4 style="margin: 0 0 15px 0; font-size: 18px; font-weight: 600;">📞 Immediate Crisis Support in Nepal:</h4>
        
        <div style="margin-bottom: 15px; padding: 12px; background: rgba(255, 255, 255, 0.1); border-radius: 8px;">
            <div style="font-weight: 600; font-size: 17px; margin-bottom: 5px;">🇳🇵 Nepal Mental Health Helpline</div>
            <div style="font-size: 24px; font-weight: 700; letter-spacing: 2px; color: #f1c40f;">1660 01 32547</div>
            <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">Mental health support and counseling</div>
        </div>
        
        <div style="margin-bottom: 15px; padding: 12px; background: rgba(255, 255, 255, 0.1); border-radius: 8px;">
            <div style="font-weight: 600; font-size: 17px; margin-bottom: 5px;">🏥 Transcultural Psychosocial Organization (TPO)</div>
            <div style="font-size: 20px; font-weight: 700;"><span style="color: #f1c40f;">01-4102803</span> / <span style="color: #f1c40f;">01-4102881</span></div>
            <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">Free mental health counseling services</div>
        </div>
        
        <div style="margin-bottom: 15px; padding: 12px; background: rgba(255, 255, 255, 0.1); border-radius: 8px;">
            <div style="font-weight: 600; font-size: 17px; margin-bottom: 5px;">💚 Patan Hospital Mental Health Unit</div>
            <div style="font-size: 20px; font-weight: 700; color: #f1c40f;">01-5522278</div>
            <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">24/7 psychiatric emergency services</div>
        </div>
        
        <div style="margin-bottom: 15px; padding: 12px; background: rgba(255, 255, 255, 0.1); border-radius: 8px;">
            <div style="font-weight: 600; font-size: 17px; margin-bottom: 5px;">🩺 Nepal Psychosocial Counseling Center</div>
            <div style="font-size: 20px; font-weight: 700; color: #f1c40f;">9851161665</div>
            <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">Confidential counseling support</div>
        </div>
        
        <div style="padding: 12px; background: rgba(241, 196, 15, 0.2); border-radius: 8px; border-left: 4px solid #f1c40f;">
            <div style="font-weight: 600; font-size: 17px; margin-bottom: 5px;">🚨 Emergency Services</div>
            <div style="font-size: 20px; font-weight: 700;">Call <span style="color: #f1c40f;">100</span> or <span style="color: #f1c40f;">102</span> (Nepal Police/Ambulance)</div>
            <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">Or visit nearest hospital emergency: Bir Hospital, Teaching Hospital, Patan Hospital</div>
        </div>
    </div>
    
    <div style="background: rgba(255, 255, 255, 0.2); border-radius: 10px; padding: 15px; text-align: center;">
        <p style="margin: 0; font-size: 16px; font-weight: 500; line-height: 1.5;">
            💙 You deserve support through this. These services won't judge you—they're here to help. 
            Please reach out right now. Your life matters.
        </p>
    </div>
</div>
"""
    
    def get_high_risk_response(self, user_message: str) -> str:
        """Response for high-risk situations with HTML formatting"""
        return """
<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 25px; border-radius: 15px; color: white; box-shadow: 0 8px 20px rgba(240, 147, 251, 0.3); margin: 10px 0;">
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <span style="font-size: 32px; margin-right: 15px;">💗</span>
        <h3 style="margin: 0; font-size: 22px; font-weight: 700;">I hear you, and you're not alone</h3>
    </div>
    
    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 20px;">
        What you're feeling is real and valid. The intensity of what you're experiencing is significant, and you shouldn't have to navigate this alone.
    </p>
    
    <div style="background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(10px); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
        <h4 style="margin: 0 0 15px 0; font-size: 18px; font-weight: 600;">🤝 Professional Support Available:</h4>
        
        <div style="margin-bottom: 12px; padding: 12px; background: rgba(255, 255, 255, 0.1); border-radius: 8px;">
            <div style="font-weight: 600; font-size: 16px;">📞 Crisis Lifeline: <span style="color: #ffd700; font-size: 20px;">988</span></div>
            <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">Call or text anytime (US)</div>
        </div>
        
        <div style="margin-bottom: 12px; padding: 12px; background: rgba(255, 255, 255, 0.1); border-radius: 8px;">
            <div style="font-weight: 600; font-size: 16px;">💬 Text Support: <span style="color: #ffd700;">HOME to 741741</span></div>
            <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">Free crisis counseling via text</div>
        </div>
        
        <div style="padding: 12px; background: rgba(255, 255, 255, 0.2); border-radius: 8px; border-left: 4px solid #ffd700;">
            <div style="font-weight: 600; font-size: 16px;">👨‍⚕️ Our 1-to-1 Professional Support</div>
            <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">Connect with licensed mental health professionals for personalized care</div>
        </div>
    </div>
    
    <div style="background: rgba(255, 255, 255, 0.2); border-radius: 10px; padding: 15px;">
        <p style="margin: 0 0 10px 0; font-size: 15px; line-height: 1.5;">
            In the meantime, I'm here to listen. Can you tell me more about what's happening right now? Sometimes talking through it can help, even in small steps.
        </p>
        <p style="margin: 0; font-size: 16px; font-weight: 600; text-align: center;">
            ✨ You matter, and things can get better.
        </p>
    </div>
</div>
"""
    
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