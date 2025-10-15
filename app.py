from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time
from chatbot import MentalHealthChatbot
import secrets
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///appointments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Store chatbot instances per session
chatbots = {}

# ============================================
# DATABASE MODELS
# ============================================
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(120), nullable=False)
    user_phone = db.Column(db.String(20), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Appointment {self.user_name} - {self.date} {self.time}>'

# Admin credentials (in production, use proper authentication)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

# ============================================
# MAIN ROUTES
# ============================================
@app.route('/')
def index():
    return render_template('index.html')

# ============================================
# CHATBOT ROUTES
# ============================================
@app.route('/ai-assessment')
def ai_assessment():
    """Route for the AI chatbot page"""
    return render_template('chatbot.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chatbot messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message.strip():
            return jsonify({'error': 'Empty message'}), 400
        
        # Get or create chatbot for this session
        session_id = session.get('chatbot_session_id')
        if not session_id:
            session_id = secrets.token_hex(8)
            session['chatbot_session_id'] = session_id
        
        if session_id not in chatbots:
            chatbots[session_id] = MentalHealthChatbot()
        
        chatbot = chatbots[session_id]
        response = chatbot.get_response(user_message)
        
        return jsonify({'response': response})
    
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred processing your message'}), 500

@app.route('/chat/reset', methods=['POST'])
def reset_chat():
    """Reset chatbot conversation"""
    try:
        session_id = session.get('chatbot_session_id')
        if session_id and session_id in chatbots:
            chatbots[session_id].reset_conversation()
            del chatbots[session_id]
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error in reset endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred resetting the conversation'}), 500

# ============================================
# APPOINTMENT ROUTES
# ============================================
@app.route('/book', methods=['GET', 'POST'])
def book_appointment():
    """Book a new appointment"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            service = request.form['service']
            date_str = request.form['date']
            time_str = request.form['time']
            message = request.form.get('message', '')

            # Convert date and time strings to proper objects
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(time_str, '%H:%M').time()

            # Check if the slot is already booked
            existing = Appointment.query.filter_by(
                date=appointment_date,
                time=appointment_time
            ).first()

            if existing:
                flash('This time slot is already booked. Please choose another time.', 'error')
                return render_template('book.html', today=date.today().isoformat())

            # Create new appointment
            appointment = Appointment(
                user_name=name,
                user_email=email,
                user_phone=phone,
                service=service,
                date=appointment_date,
                time=appointment_time,
                message=message
            )

            db.session.add(appointment)
            db.session.commit()

            flash('Appointment booked successfully! You will receive a confirmation email soon.', 'success')
            return redirect(url_for('booking_success', appt_id=appointment.id))

        except Exception as e:
            print(f"Error booking appointment: {str(e)}")
            flash('Error booking appointment. Please try again.', 'error')
            return render_template('book.html', today=date.today().isoformat())

    return render_template('book.html', today=date.today().isoformat())

@app.route('/success/<int:appt_id>')
def booking_success(appt_id):
    """Show booking success page"""
    appointment = Appointment.query.get_or_404(appt_id)
    return render_template('success.html', appointment=appointment)

@app.route('/check-status', methods=['GET', 'POST'])
def check_status():
    """Check appointment status"""
    appointment = None
    if request.method == 'POST':
        email = request.form['email']
        appointment_id = request.form.get('appointment_id')
        
        if appointment_id:
            appointment = Appointment.query.filter_by(
                id=appointment_id,
                user_email=email
            ).first()
        else:
            # Get the most recent appointment for this email
            appointment = Appointment.query.filter_by(
                user_email=email
            ).order_by(Appointment.created_at.desc()).first()
        
        if not appointment:
            flash('No appointment found with that information.', 'error')
    
    return render_template('check_status.html', appointment=appointment)

# ============================================
# ADMIN ROUTES
# ============================================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard - view all appointments"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    # Get all appointments, ordered by date and time
    appointments = Appointment.query.order_by(
        Appointment.date.asc(),
        Appointment.time.asc()
    ).all()
    
    return render_template('admin_dashboard.html', appointments=appointments)

@app.route('/admin/update-status/<int:appt_id>', methods=['POST'])
def update_status(appt_id):
    """Update appointment status"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    appointment = Appointment.query.get_or_404(appt_id)
    new_status = request.form['status']
    appointment.status = new_status
    db.session.commit()
    
    flash(f'Appointment status updated to {new_status}', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:appt_id>')
def delete_appointment(appt_id):
    """Delete an appointment"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    appointment = Appointment.query.get_or_404(appt_id)
    db.session.delete(appointment)
    db.session.commit()
    
    flash('Appointment deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin', None)
    return redirect(url_for('index'))

# ============================================
# HEALTH CHECK
# ============================================
@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

# ============================================
# DATABASE INITIALIZATION
# ============================================
def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

# ============================================
# APPLICATION STARTUP
# ============================================
if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', debug=True, port=5000)