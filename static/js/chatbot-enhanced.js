const STORAGE_KEY = "mental_health_chatbot_state";
let currentState = {
    conversation_history: [],
    mood_history: [],
    journal_entries: [],
    user_profile: {},
    positive_moments: [],
    session_count: 0
};

document.addEventListener('DOMContentLoaded', function() {
    loadState();
    restoreChat();
    updateStats();
    
    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    document.getElementById('messageInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

// ============================================
// STATE MANAGEMENT
// ============================================

function saveState() {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(currentState));
    } catch (e) {
        console.error("Error saving state:", e);
    }
}

function loadState() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            currentState = JSON.parse(saved);
        }
    } catch (e) {
        console.error("Error loading state:", e);
    }
}

function updateStats() {
    document.getElementById('sessionCount').textContent = currentState.session_count || 0;
    document.getElementById('moodCount').textContent = currentState.mood_history?.length || 0;
    document.getElementById('journalCount').textContent = currentState.journal_entries?.length || 0;
    document.getElementById('goalsCount').textContent = currentState.user_profile?.goals?.length || 0;
}

// ============================================
// CHAT FUNCTIONALITY
// ============================================

function addMessage(content, isUser = false) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'ai'}`;
    messageDiv.innerHTML = `
        <div class="message-avatar">${isUser ? 'You' : 'AI'}</div>
        <div class="message-content">
            ${isUser ? content : (content.startsWith('🤖') ? content : '🤖 ' + content)}
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showSuggestions(suggestions) {
    const suggestionsBar = document.getElementById('suggestionsBar');
    const container = document.getElementById('suggestionsContainer');
    
    if (!suggestions || suggestions.length === 0) {
        suggestionsBar.style.display = 'none';
        return;
    }
    
    const suggestionLabels = {
        'breathing_exercise': '🌬️ Breathing Exercise',
        'grounding_technique': '🧘 Grounding Technique',
        'safety_plan': '🛡️ Safety Plan',
        'gratitude_journal': '📝 Gratitude Journal',
        'positive_activities': '✨ Positive Activities',
        'mood_tracker': '😊 Mood Tracker',
        'meditation': '🧘 Meditation',
        'anxiety_tools': '💚 Anxiety Tools',
        'journal_entry': '📔 Journal Entry',
        'crisis_resources': '🆘 Crisis Resources'
    };
    
    container.innerHTML = '';
    suggestions.forEach(suggestion => {
        const chip = document.createElement('button');
        chip.className = 'suggestion-chip';
        chip.textContent = suggestionLabels[suggestion] || suggestion;
        chip.onclick = () => handleSuggestion(suggestion);
        container.appendChild(chip);
    });
    
    suggestionsBar.style.display = 'flex';
}

function handleSuggestion(suggestion) {
    const actions = {
        'breathing_exercise': () => showBreathingExercise(),
        'grounding_technique': () => showGroundingTechnique(),
        'mood_tracker': () => openModal('moodModal'),
        'journal_entry': () => openModal('journalModal'),
        'gratitude_journal': () => openGratitudeJournal(),
        'crisis_resources': () => showCrisisResources()
    };
    
    if (actions[suggestion]) {
        actions[suggestion]();
    } else {
        document.getElementById('messageInput').value = `Tell me more about ${suggestion}`;
    }
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    addMessage(message, true);
    input.value = '';
    input.disabled = true;
    document.getElementById('sendBtn').disabled = true;
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) throw new Error('Network error');
        
        const data = await response.json();
        
        addMessage(data.response);
        
        if (data.suggestions) {
            showSuggestions(data.suggestions);
        }
        
        if (data.conversation_history) {
            currentState.conversation_history = data.conversation_history;
            currentState.session_count = (currentState.session_count || 0) + 1;
            saveState();
            updateStats();
        }
        
    } catch (error) {
        console.error('Error:', error);
        addMessage('Sorry, I encountered an error. Please try again.');
    } finally {
        input.disabled = false;
        document.getElementById('sendBtn').disabled = false;
        input.focus();
    }
}

function restoreChat() {
    if (currentState.conversation_history && currentState.conversation_history.length > 0) {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';
        
        currentState.conversation_history.forEach(msg => {
            addMessage(msg.content, msg.role === 'user');
        });
        
        // Load state to server
        fetch('/chat/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ state: currentState })
        }).catch(console.error);
    }
}

async function clearChat() {
    if (!confirm('Clear chat history? Your mood tracking and journal entries will be preserved.')) return;
    
    try {
        await fetch('/chat/reset', { method: 'POST' });
        
        currentState.conversation_history = [];
        saveState();
        
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';
        addMessage('Hello! I\'m here to provide mental health support and guidance. How are you feeling today?');
        
        document.getElementById('suggestionsBar').style.display = 'none';
        
    } catch (error) {
        console.error('Error clearing chat:', error);
    }
}

// ============================================
// MOOD TRACKING
// ============================================

function quickMood(mood) {
    trackMood(mood, '');
    
    // Visual feedback
    const buttons = document.querySelectorAll('.mood-btn');
    buttons.forEach(btn => btn.classList.remove('selected'));
    event.target.classList.add('selected');
    
    setTimeout(() => {
        event.target.classList.remove('selected');
    }, 2000);
}

async function trackMood(mood, note) {
    try {
        const response = await fetch('/mood/track', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mood, note })
        });
        
        if (!response.ok) throw new Error('Failed to track mood');
        
        const data = await response.json();
        
        if (!currentState.mood_history) currentState.mood_history = [];
        currentState.mood_history.push(data.mood_entry);
        saveState();
        updateStats();
        
        showNotification('Mood tracked successfully! 😊');
        
    } catch (error) {
        console.error('Error tracking mood:', error);
        showNotification('Failed to track mood', 'error');
    }
}

function saveMood() {
    const mood = document.getElementById('moodSelect').value;
    const note = document.getElementById('moodNote').value;
    
    trackMood(mood, note);
    
    document.getElementById('moodNote').value = '';
    closeModal('moodModal');
}

// ============================================
// JOURNAL
// ============================================

async function saveJournal() {
    const title = document.getElementById('journalTitle').value;
    const content = document.getElementById('journalContent').value;
    
    if (!content.trim()) {
        showNotification('Please write something first', 'error');
        return;
    }
    
    try {
        const response = await fetch('/journal/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content })
        });
        
        if (!response.ok) throw new Error('Failed to save journal');
        
        const data = await response.json();
        
        if (!currentState.journal_entries) currentState.journal_entries = [];
        currentState.journal_entries.push(data.entry);
        saveState();
        updateStats();
        
        showNotification('Journal entry saved! 📝');
        
        document.getElementById('journalTitle').value = '';
        document.getElementById('journalContent').value = '';
        closeModal('journalModal');
        
    } catch (error) {
        console.error('Error saving journal:', error);
        showNotification('Failed to save journal entry', 'error');
    }
}

// ============================================
// GOALS
// ============================================

async function saveGoal() {
    const goal = document.getElementById('goalInput').value;
    
    if (!goal.trim()) {
        showNotification('Please enter a goal', 'error');
        return;
    }
    
    try {
        const response = await fetch('/goals/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ goal })
        });
        
        if (!response.ok) throw new Error('Failed to add goal');
        
        const data = await response.json();
        
        if (!currentState.user_profile) currentState.user_profile = {};
        currentState.user_profile.goals = data.goals;
        saveState();
        updateStats();
        
        showNotification('Goal added! 🎯');
        
        document.getElementById('goalInput').value = '';
        closeModal('goalModal');
        
    } catch (error) {
        console.error('Error adding goal:', error);
        showNotification('Failed to add goal', 'error');
    }
}

// ============================================
// POSITIVE MOMENTS
// ============================================

async function savePositiveMoment() {
    const moment = document.getElementById('positiveInput').value;
    
    if (!moment.trim()) {
        showNotification('Please share something positive', 'error');
        return;
    }
    
    try {
        const response = await fetch('/positive-moment/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ moment })
        });
        
        if (!response.ok) throw new Error('Failed to save moment');
        
        const data = await response.json();
        
        if (!currentState.positive_moments) currentState.positive_moments = [];
        currentState.positive_moments.push(data.moment);
        saveState();
        
        showNotification('Positive moment saved! ✨');
        
        document.getElementById('positiveInput').value = '';
        closeModal('positiveModal');
        
    } catch (error) {
        console.error('Error saving moment:', error);
        showNotification('Failed to save moment', 'error');
    }
}

// ============================================
// PROFILE
// ============================================

async function saveProfile() {
    const name = document.getElementById('profileName').value;
    const pronouns = document.getElementById('profilePronouns').value;
    
    try {
        const response = await fetch('/profile/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                preferred_name: name || null,
                pronouns: pronouns || null
            })
        });
        
        if (!response.ok) throw new Error('Failed to update profile');
        
        const data = await response.json();
        currentState.user_profile = data.profile;
        saveState();
        
        showNotification('Profile updated! 👤');
        closeModal('profileModal');
        
    } catch (error) {
        console.error('Error updating profile:', error);
        showNotification('Failed to update profile', 'error');
    }
}

// ============================================
// PROGRESS & INSIGHTS
// ============================================

async function viewProgress() {
    try {
        const response = await fetch('/progress/report');
        if (!response.ok) throw new Error('Failed to get progress');
        
        const data = await response.json();
        
        let report = `📊 Your Mental Health Journey\n\n`;
        report += `Total Sessions: ${data.total_sessions}\n`;
        report += `Conversations: ${data.total_conversations}\n`;
        report += `Mood Entries: ${data.mood_entries}\n`;
        report += `Journal Entries: ${data.journal_entries}\n`;
        report += `Positive Moments: ${data.positive_moments}\n`;
        report += `Goals Set: ${data.goals_set}\n`;
        
        if (data.recent_mood_summary && data.recent_mood_summary.most_common_mood) {
            report += `\nMost Common Mood (7 days): ${data.recent_mood_summary.most_common_mood}`;
        }
        
        alert(report);
        
    } catch (error) {
        console.error('Error viewing progress:', error);
        showNotification('Failed to load progress report', 'error');
    }
}

async function exportData() {
    try {
        const response = await fetch('/state/export');
        if (!response.ok) throw new Error('Failed to export');
        
        const data = await response.json();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mental-health-data-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        
        showNotification('Data exported successfully! 📥');
        
    } catch (error) {
        console.error('Error exporting data:', error);
        showNotification('Failed to export data', 'error');
    }
}

// ============================================
// WELLNESS EXERCISES
// ============================================

function showBreathingExercise() {
    addMessage('Let\'s do a simple breathing exercise together:\n\n' +
        '1. Breathe in slowly through your nose for 4 counts\n' +
        '2. Hold your breath for 4 counts\n' +
        '3. Breathe out slowly through your mouth for 6 counts\n' +
        '4. Repeat 5 times\n\n' +
        'Take your time. I\'ll be here when you\'re done. 🌬️');
}

function showGroundingTechnique() {
    addMessage('Here\'s the 5-4-3-2-1 grounding technique:\n\n' +
        '5 things you can SEE around you\n' +
        '4 things you can TOUCH\n' +
        '3 things you can HEAR\n' +
        '2 things you can SMELL\n' +
        '1 thing you can TASTE\n\n' +
        'Take your time with each step. This helps bring you back to the present moment. 🧘');
}

function showCrisisResources() {
    addMessage('🆘 Crisis Resources:\n\n' +
        '• 988: Suicide & Crisis Lifeline (US)\n' +
        '• Crisis Text Line: Text HOME to 741741\n' +
        '• International: findahelpline.com\n\n' +
        'You\'re not alone. Please reach out if you\'re in crisis.');
}

function openGratitudeJournal() {
    document.getElementById('journalTitle').value = 'Gratitude - ' + new Date().toLocaleDateString();
    document.getElementById('journalContent').placeholder = 'What are you grateful for today?';
    openModal('journalModal');
}

// ============================================
// MODAL MANAGEMENT
// ============================================

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Close modal on outside click
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// ============================================
// NOTIFICATIONS
// ============================================

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#4CAF50' : '#f44336'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}