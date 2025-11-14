from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mail import Mail, Message
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from email_service import init_mail, send_appointment_confirmation, send_contact_confirmation
import secrets
import os
import sys

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///appointments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@mentalhealth.com')

# Import models and initialize db (MUST be after app config)
from models import db, User, Professional, Appointment, Review, Contact
db.init_app(app)

# Initialize email
from email_service import init_mail, send_appointment_confirmation
init_mail(app)

mail = Mail(app)

# Store chatbot instances per session
chatbots = {}

from contact_routes import add_contact_routes
add_contact_routes(app)

# ============================================
# DATABASE MODELS
# ============================================

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

# ============================================
# DECORATORS
# ============================================
def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# EMAIL FUNCTIONS
# ============================================
def send_appointment_confirmation(appointment):
    """Send appointment confirmation email"""
    try:
        subject = f"Appointment Confirmation - #{appointment.id}"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #d4a574, #c8956d); color: white; padding: 30px; text-align: center;">
                <h1>🎉 Appointment Confirmed!</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <p>Dear {appointment.user_name},</p>
                <p>Your appointment has been scheduled successfully!</p>
                <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #c8956d;">Appointment Details</h3>
                    <p><strong>ID:</strong> #{appointment.id}</p>
                    <p><strong>Professional:</strong> {appointment.professional.name}</p>
                    <p><strong>Date:</strong> {appointment.date.strftime('%B %d, %Y')}</p>
                    <p><strong>Time:</strong> {appointment.time.strftime('%I:%M %p')}</p>
                    <p><strong>Service:</strong> {appointment.service}</p>
                    <p><strong>Status:</strong> {appointment.status}</p>
                </div>
                <p>Please arrive 5-10 minutes before your scheduled time.</p>
            </div>
        </div>
        """
        
        msg = Message(subject, recipients=[appointment.user_email])
        msg.html = html_body
        mail.send(msg)
        
        appointment.confirmation_sent = True
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {str(e)}")
        return False

def send_status_update_email(appointment, old_status, new_status):
    """Send email when appointment status changes"""
    try:
        subject = f"Appointment Status Update - #{appointment.id}"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #27ae60; color: white; padding: 30px; text-align: center;">
                <h1>Status Updated</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <p>Dear {appointment.user_name},</p>
                <p>Your appointment status has been updated:</p>
                <p><strong>Previous Status:</strong> {old_status}</p>
                <p><strong>New Status:</strong> {new_status}</p>
                <p><strong>Appointment ID:</strong> #{appointment.id}</p>
                <p><strong>Date:</strong> {appointment.date.strftime('%B %d, %Y')} at {appointment.time.strftime('%I:%M %p')}</p>
            </div>
        </div>
        """
        
        msg = Message(subject, recipients=[appointment.user_email])
        msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending status update email: {str(e)}")
        return False

def send_review_request_email(appointment):
    """Send email requesting review after completed appointment"""
    try:
        subject = "How was your session? Leave a review"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #ffc107, #ff9800); color: white; padding: 30px; text-align: center;">
                <h1>⭐ Share Your Experience</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <p>Dear {appointment.user_name},</p>
                <p>Thank you for your session with {appointment.professional.name}!</p>
                <p>Your feedback helps others find the right professional. Please take a moment to leave a review.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="http://localhost:5000/leave-review/{appointment.id}" 
                       style="background: linear-gradient(135deg, #ffc107, #ff9800); color: white; 
                              padding: 15px 30px; text-decoration: none; border-radius: 10px; 
                              display: inline-block; font-weight: bold;">Leave a Review</a>
                </div>
            </div>
        </div>
        """
        
        msg = Message(subject, recipients=[appointment.user_email])
        msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending review request email: {str(e)}")
        return False

# ============================================
# MAIN ROUTES
# ============================================
@app.route('/')
def index():
    return render_template('index.html')

# ============================================
# USER AUTHENTICATION ROUTES
# ============================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            
            if not all([name, email, phone, password]):
                flash('All fields are required.', 'danger')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('register.html')
            
            if len(password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return render_template('register.html')
            
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already registered. Please login.', 'danger')
                return redirect(url_for('login'))
            
            user = User(name=name, email=email, phone=phone)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during registration: {str(e)}")
            flash('An error occurred. Please try again.', 'danger')
    
    return render_template('register.html')

@app.route('/profile')
@login_required
def user_profile():
    """User profile page"""
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    
    return render_template('user_profile.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            
            flash(f'Welcome back, {user.name}!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('user_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    user_name = session.get('user_name', 'User')
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    
    flash(f'Goodbye, {user_name}! You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def user_dashboard():
    """User dashboard - view appointments"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    appointments = Appointment.query.filter_by(user_id=user_id).order_by(
        Appointment.date.desc(),
        Appointment.time.desc()
    ).all()
    
    today = date.today()
    upcoming = [a for a in appointments if a.date >= today and a.status not in ['Cancelled', 'Completed']]
    past = [a for a in appointments if a.date < today or a.status in ['Cancelled', 'Completed']]
    
    return render_template('user_dashboard.html', 
                         user=user, 
                         upcoming_appointments=upcoming,
                         past_appointments=past)

@app.route('/appointment/<int:appt_id>')
@login_required
def view_appointment(appt_id):
    """View appointment details"""
    user_id = session.get('user_id')
    appointment = Appointment.query.get_or_404(appt_id)
    
    if appointment.user_id != user_id:
        flash('You do not have permission to view this appointment.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    return render_template('appointment_detail.html', appointment=appointment)

@app.route('/appointment/<int:appt_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appt_id):
    """Cancel an appointment"""
    user_id = session.get('user_id')
    appointment = Appointment.query.get_or_404(appt_id)
    
    if appointment.user_id != user_id:
        flash('You do not have permission to cancel this appointment.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    appointment_datetime = datetime.combine(appointment.date, appointment.time)
    now = datetime.now()
    
    if appointment_datetime < now:
        flash('Cannot cancel past appointments.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    if (appointment_datetime - now) < timedelta(hours=24):
        flash('Appointments must be cancelled at least 24 hours in advance.', 'warning')
        return redirect(url_for('user_dashboard'))
    
    old_status = appointment.status
    appointment.status = 'Cancelled'
    appointment.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    send_status_update_email(appointment, old_status, 'Cancelled')
    
    flash('Appointment cancelled successfully.', 'success')
    return redirect(url_for('user_dashboard'))

# ============================================
# PROFESSIONAL ROUTES
# ============================================
@app.route('/professionals')
def professionals():
    """Display all active professionals"""
    all_professionals = Professional.query.filter_by(is_active=True).order_by(Professional.name).all()
    return render_template('professionals.html', professionals=all_professionals)

@app.route('/professional/<int:prof_id>')
def professional_detail(prof_id):
    """Display detailed profile of a professional"""
    prof = Professional.query.get_or_404(prof_id)
    
    reviews = Review.query.filter_by(
        professional_id=prof_id,
        is_approved=True
    ).order_by(Review.created_at.desc()).limit(5).all()
    
    return render_template('professional_detail.html', professional=prof, reviews=reviews)

@app.route('/professional/<int:prof_id>/reviews')
def professional_reviews(prof_id):
    """View all reviews for a professional"""
    professional = Professional.query.get_or_404(prof_id)
    
    reviews = Review.query.filter_by(
        professional_id=prof_id,
        is_approved=True
    ).order_by(Review.created_at.desc()).all()
    
    return render_template('professional_reviews.html', 
                         professional=professional,
                         reviews=reviews)

# ============================================
# REVIEW ROUTES
# ============================================
@app.route('/leave-review/<int:appt_id>', methods=['GET', 'POST'])
def leave_review(appt_id):
    """Leave a review for a completed appointment"""
    appointment = Appointment.query.get_or_404(appt_id)
    
    if appointment.status != 'Completed':
        flash('You can only review completed appointments.', 'warning')
        return redirect(url_for('index'))
    
    existing_review = Review.query.filter_by(appointment_id=appt_id).first()
    if existing_review:
        flash('You have already reviewed this appointment.', 'info')
        return redirect(url_for('professional_detail', prof_id=appointment.professional_id))
    
    if request.method == 'POST':
        try:
            rating = int(request.form['rating'])
            comment = request.form.get('comment', '').strip()
            is_anonymous = 'is_anonymous' in request.form
            
            if rating < 1 or rating > 5:
                flash('Please provide a rating between 1 and 5 stars.', 'danger')
                return render_template('leave_review.html', appointment=appointment)
            
            review = Review(
                user_id=appointment.user_id,
                professional_id=appointment.professional_id,
                appointment_id=appointment.id,
                rating=rating,
                comment=comment if comment else None,
                is_anonymous=is_anonymous,
                is_approved=True
            )
            
            db.session.add(review)
            
            professional = Professional.query.get(appointment.professional_id)
            professional.update_rating()
            
            db.session.commit()
            
            flash('Thank you for your review! Your feedback helps others.', 'success')
            return redirect(url_for('professional_detail', prof_id=appointment.professional_id))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error submitting review: {str(e)}")
            flash('An error occurred. Please try again.', 'danger')
    
    return render_template('leave_review.html', appointment=appointment)

# ============================================
# CHATBOT BOOKING ROUTES (ADD THESE TO YOUR APP.PY)
# ============================================

from flask import render_template, request, jsonify, session
from chatbot import MentalHealthChatbot
from datetime import datetime
import secrets

# Import db, Professional, and Appointment from your existing models
# These should already be imported at the top of your app.py

# Store chatbot instances per session
chatbots = {}

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
        
        # Get or create session ID
        session_id = session.get('chatbot_session_id')
        if not session_id:
            session_id = secrets.token_hex(8)
            session['chatbot_session_id'] = session_id
        
        # Create chatbot instance if it doesn't exist
        if session_id not in chatbots:
            chatbots[session_id] = MentalHealthChatbot()
            print(f"✓ Created new chatbot session: {session_id}")
        
        # Get response from chatbot
        chatbot = chatbots[session_id]
        response = chatbot.get_response(user_message)
        
        # Check if booking is complete
        booking_complete = False
        conversation_history = chatbot.get_conversation_history()
        if conversation_history and len(conversation_history) > 0:
            last_msg = conversation_history[-1]
            if last_msg.get('booking_complete'):
                booking_complete = True
        
        # Return response with conversation history for client-side storage
        return jsonify({
            'response': response,
            'conversation_history': conversation_history,
            'booking_complete': booking_complete
        })
    
    except Exception as e:
        print(f"❌ Error in chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return user-friendly error with crisis resources
        return jsonify({
            'error': 'I apologize, I\'m experiencing technical difficulties. Please try again in a moment.',
            'crisis_resources': (
                'If you need immediate support:\n'
                '• 988: Suicide & Crisis Lifeline\n'
                '• Crisis Text Line: Text HOME to 741741'
            )
        }), 500

@app.route('/api/professionals', methods=['GET'])
def api_professionals():
    """API endpoint to get all active professionals for chatbot booking"""
    try:
        # Query active professionals
        professionals = Professional.query.filter_by(is_active=True).order_by(Professional.name).all()
        
        print(f"📊 Found {len(professionals)} active professionals")
        
        # Build response list
        prof_list = []
        for prof in professionals:
            prof_data = {
                'id': prof.id,
                'name': prof.name,
                'title': prof.title,
                'specialization': prof.specialization,
                'experience_years': prof.experience_years,
                'rating': float(prof.rating) if prof.rating else 5.0,
                'total_reviews': prof.total_reviews if prof.total_reviews else 0,
                'languages': prof.languages,
                'available_days': prof.available_days
            }
            prof_list.append(prof_data)
            print(f"  ✓ Added: {prof.name}")
        
        print(f"✅ Returning {len(prof_list)} professionals")
        return jsonify(prof_list), 200
    
    except Exception as e:
        print(f"❌ Error in /api/professionals: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Could not fetch professionals',
            'message': str(e)
        }), 500
        
        

@app.route('/chat/complete-booking', methods=['POST'])
def complete_booking():
    """Complete the appointment booking from chatbot"""
    try:
        # Get session ID
        session_id = session.get('chatbot_session_id')
        if not session_id or session_id not in chatbots:
            return jsonify({'error': 'Invalid session'}), 400
        
        # Get booking data from chatbot
        chatbot = chatbots[session_id]
        booking_data = chatbot.get_booking_data()
        
        if not booking_data:
            return jsonify({'error': 'No booking data found'}), 400
        
        # Validate required fields
        required_fields = ['professional_id', 'name', 'email', 'phone', 'service', 'date', 'time']
        for field in required_fields:
            if field not in booking_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Convert date and time strings to proper types
        appointment_date = datetime.strptime(booking_data['date'], '%Y-%m-%d').date()
        appointment_time = datetime.strptime(booking_data['time'], '%H:%M').time()
        
        # Check if professional exists
        professional = Professional.query.get(booking_data['professional_id'])
        if not professional:
            return jsonify({'error': 'Professional not found'}), 404
        
        # Check for existing appointment at same time
        existing = Appointment.query.filter_by(
            professional_id=booking_data['professional_id'],
            date=appointment_date,
            time=appointment_time
        ).first()
        
        if existing:
            return jsonify({
                'error': 'This time slot is already booked',
                'message': 'This time slot is already booked. Please choose another time.'
            }), 409
        
        # Get user_id if logged in
        user_id = session.get('user_id')
        
        # Create appointment
        appointment = Appointment(
            user_id=user_id,
            user_name=booking_data['name'],
            user_email=booking_data['email'],
            user_phone=booking_data['phone'],
            service=booking_data['service'],
            professional_id=booking_data['professional_id'],
            date=appointment_date,
            time=appointment_time,
            message="Booked via AI Chatbot"
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        # Send confirmation email (if you have email service set up)
        try:
            from email_service import send_appointment_confirmation
            send_appointment_confirmation(appointment)
        except ImportError:
            print("Email service not available")
        except Exception as e:
            print(f"Error sending confirmation email: {str(e)}")
        
        # Reset booking state in chatbot
        chatbot.reset_booking()
        
        # Return success response
        return jsonify({
            'success': True,
            'appointment_id': appointment.id,
            'message': 'Appointment booked successfully!',
            'appointment': {
                'id': appointment.id,
                'professional_name': professional.name,
                'date': appointment.date.strftime('%B %d, %Y'),
                'time': appointment.time.strftime('%I:%M %p'),
                'service': appointment.service,
                'status': appointment.status
            }
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error completing booking: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to complete booking. Please try again.'}), 500

@app.route('/chat/cancel-booking', methods=['POST'])
def cancel_booking():
    """Cancel the current booking process"""
    try:
        session_id = session.get('chatbot_session_id')
        if session_id and session_id in chatbots:
            chatbot = chatbots[session_id]
            chatbot.reset_booking()
        
        return jsonify({'success': True, 'message': 'Booking cancelled'})
    
    except Exception as e:
        print(f"❌ Error cancelling booking: {str(e)}")
        return jsonify({'error': 'Could not cancel booking'}), 500

@app.route('/chat/load', methods=['POST'])
def load_chat_history():
    """Load conversation history from client (localStorage) into server session"""
    try:
        data = request.get_json()
        history = data.get('history', [])
        
        if not history:
            return jsonify({'status': 'success', 'message': 'No history to load'})
        
        # Get or create session ID
        session_id = session.get('chatbot_session_id')
        if not session_id:
            session_id = secrets.token_hex(8)
            session['chatbot_session_id'] = session_id
        
        # Create chatbot instance if it doesn't exist
        if session_id not in chatbots:
            chatbots[session_id] = MentalHealthChatbot()
            print(f"✓ Created new chatbot session: {session_id}")
        
        # Load the history into the chatbot
        chatbot = chatbots[session_id]
        chatbot.load_conversation_history(history)
        
        print(f"✓ Loaded {len(history)} messages into session: {session_id}")
        
        return jsonify({
            'status': 'success',
            'message': f'Loaded {len(history)} messages',
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"❌ Error loading chat history: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Could not load chat history'}), 500

@app.route('/chat/reset', methods=['POST'])
def reset_chat():
    """Reset chatbot conversation"""
    try:
        session_id = session.get('chatbot_session_id')
        
        if session_id and session_id in chatbots:
            chatbots[session_id].reset_conversation()
            del chatbots[session_id]
            print(f"✓ Reset chatbot session: {session_id}")
        
        # Clear session ID so a new chatbot will be created
        session.pop('chatbot_session_id', None)
        
        return jsonify({'status': 'success', 'message': 'Conversation reset successfully'})
        
    except Exception as e:
        print(f"❌ Error in reset endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'An error occurred resetting the conversation'}), 500

@app.route('/chat/history', methods=['GET'])
def get_chat_history():
    """Get conversation history for current session"""
    try:
        session_id = session.get('chatbot_session_id')
        
        if session_id and session_id in chatbots:
            history = chatbots[session_id].get_conversation_history()
            return jsonify({'history': history})
        
        return jsonify({'history': []})
        
    except Exception as e:
        print(f"❌ Error getting chat history: {str(e)}")
        return jsonify({'error': 'Could not retrieve chat history'}), 500

@app.route('/chat/crisis-count', methods=['GET'])
def get_crisis_count():
    """Get number of crisis alerts detected in current session"""
    try:
        session_id = session.get('chatbot_session_id')
        
        if session_id and session_id in chatbots:
            count = chatbots[session_id].get_crisis_alert_count()
            return jsonify({'crisis_count': count})
        
        return jsonify({'crisis_count': 0})
        
    except Exception as e:
        print(f"❌ Error getting crisis count: {str(e)}")
        return jsonify({'error': 'Could not retrieve crisis count'}), 500
    
# ============================================
# APPOINTMENT ROUTES
# ============================================
@app.route('/book', methods=['GET'])
def book_appointment():
    """Redirect to professionals page to select a professional first"""
    return redirect(url_for('professionals'))

@app.route('/book/<int:prof_id>', methods=['GET', 'POST'])
def book_with_professional(prof_id):
    """Book appointment with a specific professional"""
    professional = Professional.query.get_or_404(prof_id)
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            service = request.form['service']
            date_str = request.form['date']
            time_str = request.form['time']
            message = request.form.get('message', '')

            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appointment_time = datetime.strptime(time_str, '%H:%M').time()

            existing = Appointment.query.filter_by(
                professional_id=prof_id,
                date=appointment_date,
                time=appointment_time
            ).first()

            if existing:
                flash('This time slot is already booked. Please choose another time.', 'error')
                return render_template('book.html', 
                                     professional=professional, 
                                     today=date.today().isoformat())

            user_id = session.get('user_id')

            appointment = Appointment(
                user_id=user_id,
                user_name=name,
                user_email=email,
                user_phone=phone,
                service=service,
                professional_id=prof_id,
                date=appointment_date,
                time=appointment_time,
                message=message
            )

            db.session.add(appointment)
            db.session.commit()

            send_appointment_confirmation(appointment)

            flash('Appointment booked successfully! Check your email for confirmation.', 'success')
            return redirect(url_for('booking_success', appt_id=appointment.id))

        except Exception as e:
            db.session.rollback()
            print(f"Error booking appointment: {str(e)}")
            flash('Error booking appointment. Please try again.', 'error')

    return render_template('book.html', 
                         professional=professional, 
                         today=date.today().isoformat())

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
    
    return render_template('admin/admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard - view all appointments"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    appointments = Appointment.query.order_by(
        Appointment.date.asc(),
        Appointment.time.asc()
    ).all()
    
    return render_template('admin/admin_dashboard.html', appointments=appointments)

@app.route('/admin/professionals')
def admin_professionals():
    """Admin page to manage professionals"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    all_professionals = Professional.query.all()
    return render_template('admin/admin_professionals.html', professionals=all_professionals)

@app.route('/admin/professional/add', methods=['GET', 'POST'])
def add_professional():
    """Add a new professional"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        try:
            required_fields = ['name', 'title', 'specialization', 'bio', 'experience_years', 'education', 'languages', 'available_days']
            
            # Check if all required fields are filled
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'Please fill in all required fields.', 'danger')
                    return render_template('admin/admin_add_professional.html')
            
            professional = Professional(
                name=request.form['name'],
                title=request.form['title'],
                specialization=request.form['specialization'],
                bio=request.form['bio'],
                experience_years=int(request.form['experience_years']),
                education=request.form['education'],
                languages=request.form['languages'],
                available_days=request.form['available_days'],
                image_url=request.form.get('image_url', 'default-avatar.jpg'),
                rating=5.0,
                total_reviews=0,
                is_active=True
            )
            
            db.session.add(professional)
            db.session.commit()
            
            flash('Professional added successfully!', 'success')
            return redirect(url_for('admin_professionals'))
            
        except ValueError as e:
            flash('Please enter a valid number for years of experience.', 'danger')
            return render_template('admin/admin_add_professional.html')
        except Exception as e:
            db.session.rollback()
            print(f"Error adding professional: {str(e)}")
            flash('Error adding professional. Please try again.', 'danger')
            return render_template('admin/admin_add_professional.html')
    
    return render_template('admin/admin_add_professional.html')

@app.route('/admin/professional/edit/<int:prof_id>', methods=['GET', 'POST'])
def edit_professional(prof_id):
    """Edit an existing professional"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    professional = Professional.query.get_or_404(prof_id)
    
    if request.method == 'POST':
        try:
            required_fields = ['name', 'title', 'specialization', 'bio', 'experience_years', 'education', 'languages', 'available_days']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'Please fill in all required fields.', 'danger')
                    return render_template('admin/admin_edit_professional.html', professional=professional)
            
            professional.name = request.form['name']
            professional.title = request.form['title']
            professional.specialization = request.form['specialization']
            professional.bio = request.form['bio']
            professional.experience_years = int(request.form['experience_years'])
            professional.education = request.form['education']
            professional.languages = request.form['languages']
            professional.available_days = request.form['available_days']
            
            if request.form.get('image_url'):
                professional.image_url = request.form['image_url']
            else:
                professional.image_url = 'default-avatar.jpg'
            
            professional.is_active = 'is_active' in request.form
            
            db.session.commit()
            
            flash(f'Professional {professional.name} updated successfully!', 'success')
            return redirect(url_for('admin_professionals'))
            
        except ValueError as e:
            flash('Please enter a valid number for years of experience.', 'danger')
            return render_template('admin/admin_edit_professional.html', professional=professional)
        except Exception as e:
            db.session.rollback()
            print(f"Error updating professional: {str(e)}")
            flash('Error updating professional. Please try again.', 'danger')
            return render_template('admin/admin_edit_professional.html', professional=professional)
    
    return render_template('admin/admin_edit_professional.html', professional=professional)

@app.route('/admin/professional/delete/<int:prof_id>')
def delete_professional(prof_id):
    """Delete a professional"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        professional = Professional.query.get_or_404(prof_id)
        
        appointment_count = Appointment.query.filter_by(professional_id=prof_id).count()
        
        if appointment_count > 0:
            flash(f'Cannot delete {professional.name}. They have {appointment_count} appointment(s) associated with them.', 'danger')
            return redirect(url_for('admin_professionals'))
        
        db.session.delete(professional)
        db.session.commit()
        
        flash(f'Professional {professional.name} deleted successfully!', 'success')
        return redirect(url_for('admin_professionals'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting professional: {str(e)}")
        flash('Error deleting professional. Please try again.', 'danger')
        return redirect(url_for('admin_professionals'))

@app.route('/admin/update-status/<int:appt_id>', methods=['POST'])
def update_status(appt_id):
    """Update appointment status"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        appointment = Appointment.query.get_or_404(appt_id)
        old_status = appointment.status
        new_status = request.form['status']
        
        appointment.status = new_status
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        send_status_update_email(appointment, old_status, new_status)
        
        if new_status == 'Completed':
            send_review_request_email(appointment)
        
        flash(f'Appointment status updated to {new_status}', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating status: {str(e)}")
        flash('Error updating status. Please try again.', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:appt_id>')
def delete_appointment(appt_id):
    """Delete an appointment"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        appointment = Appointment.query.get_or_404(appt_id)
        db.session.delete(appointment)
        db.session.commit()
        
        flash('Appointment deleted successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting appointment: {str(e)}")
        flash('Error deleting appointment. Please try again.', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reviews')
def admin_reviews():
    """Admin page to moderate reviews"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    
    return render_template('admin/admin_reviews.html', reviews=reviews)

@app.route('/admin/review/<int:review_id>/approve', methods=['POST'])
def approve_review(review_id):
    """Approve a review"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        review = Review.query.get_or_404(review_id)
        review.is_approved = True
        
        professional = Professional.query.get(review.professional_id)
        professional.update_rating()
        
        db.session.commit()
        
        flash('Review approved successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error approving review: {str(e)}")
        flash('An error occurred.', 'danger')
    
    return redirect(url_for('admin_reviews'))

@app.route('/admin/review/<int:review_id>/reject', methods=['POST'])
def reject_review(review_id):
    """Reject/delete a review"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        review = Review.query.get_or_404(review_id)
        professional_id = review.professional_id
        
        db.session.delete(review)
        
        professional = Professional.query.get(professional_id)
        professional.update_rating()
        
        db.session.commit()
        
        flash('Review deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting review: {str(e)}")
        flash('An error occurred.', 'danger')
    
    return redirect(url_for('admin_reviews'))

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
        
        # Add sample professionals if none exist
        if Professional.query.count() == 0:
            sample_professionals = [
                Professional(
                    name="Dr. Sarah Johnson",
                    title="Licensed Clinical Psychologist",
                    specialization="Anxiety, Depression, Trauma & PTSD",
                    bio="Dr. Sarah Johnson is a compassionate clinical psychologist with over 12 years of experience helping individuals overcome anxiety, depression, and trauma. She uses evidence-based approaches including CBT and mindfulness techniques.",
                    experience_years=12,
                    education="Ph.D. in Clinical Psychology, Harvard University; M.A. in Psychology, Stanford University",
                    languages="English, Spanish",
                    available_days="Monday, Tuesday, Wednesday, Thursday, Friday",
                    rating=4.9,
                    total_reviews=127
                ),
                Professional(
                    name="Dr. Michael Chen",
                    title="Psychiatrist",
                    specialization="Mood Disorders, Bipolar, Medication Management",
                    bio="Dr. Michael Chen specializes in treating mood disorders and provides comprehensive psychiatric care. He believes in a holistic approach combining medication management with therapy.",
                    experience_years=15,
                    education="M.D., Johns Hopkins School of Medicine; Psychiatry Residency, Mayo Clinic",
                    languages="English, Mandarin, Cantonese",
                    available_days="Monday, Wednesday, Friday",
                    rating=4.8,
                    total_reviews=98
                ),
                Professional(
                    name="Dr. Emily Rodriguez",
                    title="Licensed Marriage and Family Therapist",
                    specialization="Relationships, Family Therapy, Couples Counseling",
                    bio="Dr. Emily Rodriguez helps couples and families navigate challenges and build stronger relationships. She creates a safe, non-judgmental space for open communication and healing.",
                    experience_years=10,
                    education="Ph.D. in Marriage and Family Therapy, UCLA; M.S. in Counseling Psychology",
                    languages="English, Spanish, Portuguese",
                    available_days="Tuesday, Thursday, Saturday",
                    rating=5.0,
                    total_reviews=156
                )
            ]
            
            for prof in sample_professionals:
                db.session.add(prof)
            
            db.session.commit()
            print("✅ Sample professionals added!")
        
        print("✅ Database tables created successfully!")
        
        
@app.route('/about')
def about():
    """About us page"""
    return render_template('about.html')

# ============================================
# APPLICATION STARTUP
# ============================================
if __name__ == '__main__':
    create_tables()
    print("\n" + "="*50)
    print("🚀 Mental Health Platform Started!")
    print("="*50)
    print("📧 Email notifications:", "Enabled" if app.config['MAIL_USERNAME'] else "Disabled (configure .env)")
    print("🔐 User authentication: Enabled")
    print("⭐ Review system: Enabled")
    print("👨‍⚕️ Professionals: Ready")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', debug=True, port=5000)