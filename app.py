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
class Professional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text, nullable=False)
    experience_years = db.Column(db.Integer, nullable=False)
    education = db.Column(db.Text, nullable=False)
    languages = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200), default='default-avatar.jpg')
    available_days = db.Column(db.String(200), nullable=False)  # JSON string of available days
    rating = db.Column(db.Float, default=5.0)
    total_reviews = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    appointments = db.relationship('Appointment', backref='professional', lazy=True)

    def __repr__(self):
        return f'<Professional {self.name}>'

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(120), nullable=False)
    user_phone = db.Column(db.String(20), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=False)
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
    return render_template('professional_detail.html', professional=prof)

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

            # Check if the slot is already booked with this professional
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

            # Create new appointment
            appointment = Appointment(
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

            flash('Appointment booked successfully! You will receive a confirmation email soon.', 'success')
            return redirect(url_for('booking_success', appt_id=appointment.id))

        except Exception as e:
            print(f"Error booking appointment: {str(e)}")
            flash('Error booking appointment. Please try again.', 'error')
            return render_template('book.html', 
                                 professional=professional, 
                                 today=date.today().isoformat())

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

@app.route('/admin/professionals')
def admin_professionals():
    """Admin page to manage professionals"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    all_professionals = Professional.query.all()
    return render_template('admin_professionals.html', professionals=all_professionals)

@app.route('/admin/professional/add', methods=['GET', 'POST'])
def add_professional():
    """Add a new professional"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['name', 'title', 'specialization', 'bio', 'experience_years', 'education', 'languages', 'available_days']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'Please fill in all required fields.', 'danger')
                    return render_template('admin_add_professional.html')
            
            # Create new professional
            professional = Professional(
                name=request.form['name'],
                title=request.form['title'],
                specialization=request.form['specialization'],
                bio=request.form['bio'],
                experience_years=int(request.form['experience_years']),
                education=request.form['education'],
                languages=request.form['languages'],
                available_days=request.form['available_days'],
                image_url=request.form.get('image_url', 'default-avatar.jpg') if request.form.get('image_url') else 'default-avatar.jpg',
                rating=5.0,  # Default rating
                total_reviews=0,  # Start with 0 reviews
                is_active=True  # Active by default
            )
            
            db.session.add(professional)
            db.session.commit()
            
            flash('Professional added successfully!', 'success')
            return redirect(url_for('admin_professionals'))
            
        except ValueError as e:
            flash('Please enter a valid number for years of experience.', 'danger')
            return render_template('admin_add_professional.html')
        except Exception as e:
            db.session.rollback()
            print(f"Error adding professional: {str(e)}")
            flash('Error adding professional. Please try again.', 'danger')
            return render_template('admin_add_professional.html')
    
    return render_template('admin_add_professional.html')

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

@app.route('/admin/professional/edit/<int:prof_id>', methods=['GET', 'POST'])
def edit_professional(prof_id):
    """Edit an existing professional"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    professional = Professional.query.get_or_404(prof_id)
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['name', 'title', 'specialization', 'bio', 'experience_years', 'education', 'languages', 'available_days']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'Please fill in all required fields.', 'danger')
                    return render_template('admin_edit_professional.html', professional=professional)
            
            # Update professional
            professional.name = request.form['name']
            professional.title = request.form['title']
            professional.specialization = request.form['specialization']
            professional.bio = request.form['bio']
            professional.experience_years = int(request.form['experience_years'])
            professional.education = request.form['education']
            professional.languages = request.form['languages']
            professional.available_days = request.form['available_days']
            
            # Update image URL if provided
            if request.form.get('image_url'):
                professional.image_url = request.form['image_url']
            else:
                professional.image_url = 'default-avatar.jpg'
            
            # Update status - checkbox is present only when checked
            professional.is_active = 'is_active' in request.form
            
            db.session.commit()
            
            flash(f'Professional {professional.name} updated successfully!', 'success')
            return redirect(url_for('admin_professionals'))
            
        except ValueError as e:
            flash('Please enter a valid number for years of experience.', 'danger')
            return render_template('admin_edit_professional.html', professional=professional)
        except Exception as e:
            db.session.rollback()
            print(f"Error updating professional: {str(e)}")
            flash('Error updating professional. Please try again.', 'danger')
            return render_template('admin_edit_professional.html', professional=professional)
    
    return render_template('admin_edit_professional.html', professional=professional)

@app.route('/admin/professional/delete/<int:prof_id>')
def delete_professional(prof_id):
    """Delete a professional"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        professional = Professional.query.get_or_404(prof_id)
        
        # Check if professional has any appointments
        appointment_count = Appointment.query.filter_by(professional_id=prof_id).count()
        
        if appointment_count > 0:
            flash(f'Cannot delete {professional.name}. They have {appointment_count} appointment(s) associated with them. Please reassign or delete those appointments first.', 'danger')
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

@app.route('/admin/professional/toggle/<int:prof_id>')
def toggle_professional_status(prof_id):
    """Toggle professional active/inactive status"""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        professional = Professional.query.get_or_404(prof_id)
        professional.is_active = not professional.is_active
        db.session.commit()
        
        status = "activated" if professional.is_active else "deactivated"
        flash(f'Professional {professional.name} {status} successfully!', 'success')
        return redirect(url_for('admin_professionals'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error toggling professional status: {str(e)}")
        flash('Error updating professional status. Please try again.', 'danger')
        return redirect(url_for('admin_professionals'))

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
            print("Sample professionals added!")
        
        print("Database tables created successfully!")

# ============================================
# APPLICATION STARTUP
# ============================================
if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', debug=True, port=5000)