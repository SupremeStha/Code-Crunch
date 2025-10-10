from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///appointments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
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

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/book', methods=['GET', 'POST'])
def book_appointment():
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
                return render_template('book.html')

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
            flash('Error booking appointment. Please try again.', 'error')
            return render_template('book.html')

    return render_template('book.html', today=date.today().isoformat())

@app.route('/success/<int:appt_id>')
def booking_success(appt_id):
    appointment = Appointment.query.get_or_404(appt_id)
    return render_template('success.html', appointment=appointment)

@app.route('/check_status', methods=['GET', 'POST'])
def check_status():
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

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
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
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    # Get all appointments, ordered by date and time
    appointments = Appointment.query.order_by(
        Appointment.date.desc(),
        Appointment.time.desc()
    ).all()
    
    return render_template('admin_dashboard.html', appointments=appointments)

@app.route('/admin/update_status/<int:appt_id>', methods=['POST'])
def update_status(appt_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    appointment = Appointment.query.get_or_404(appt_id)
    new_status = request.form['status']
    appointment.status = new_status
    db.session.commit()
    
    flash(f'Appointment status updated to {new_status}', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/admin/delete/<int:appt_id>')
def delete_appointment(appt_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    appointment = Appointment.query.get_or_404(appt_id)
    db.session.delete(appointment)
    db.session.commit()
    
    flash('Appointment deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

# Create database tables
def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)