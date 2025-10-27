# auth_routes.py - User authentication routes
from flask import render_template, request, redirect, url_for, flash, session
from models import db, User, Appointment
from functools import wraps

def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def add_auth_routes(app):
    """Add authentication routes to the Flask app"""
    
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
                
                # Validation
                if not all([name, email, phone, password]):
                    flash('All fields are required.', 'danger')
                    return render_template('register.html')
                
                if password != confirm_password:
                    flash('Passwords do not match.', 'danger')
                    return render_template('register.html')
                
                if len(password) < 6:
                    flash('Password must be at least 6 characters.', 'danger')
                    return render_template('register.html')
                
                # Check if user exists
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    flash('Email already registered. Please login.', 'danger')
                    return redirect(url_for('login'))
                
                # Create new user
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
        
        return render_template('register.html')
    
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
                
                # Redirect to dashboard or requested page
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
        
        # Get user's appointments
        appointments = Appointment.query.filter_by(user_id=user_id).order_by(
            Appointment.date.desc(),
            Appointment.time.desc()
        ).all()
        
        # Separate upcoming and past appointments
        from datetime import date
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
        
        # Check if appointment belongs to user
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
        
        # Check if appointment belongs to user
        if appointment.user_id != user_id:
            flash('You do not have permission to cancel this appointment.', 'danger')
            return redirect(url_for('user_dashboard'))
        
        # Check if appointment can be cancelled
        from datetime import date, datetime, timedelta
        appointment_datetime = datetime.combine(appointment.date, appointment.time)
        now = datetime.now()
        
        if appointment_datetime < now:
            flash('Cannot cancel past appointments.', 'danger')
            return redirect(url_for('user_dashboard'))
        
        if (appointment_datetime - now) < timedelta(hours=24):
            flash('Appointments must be cancelled at least 24 hours in advance.', 'warning')
            return redirect(url_for('user_dashboard'))
        
        # Cancel the appointment
        old_status = appointment.status
        appointment.status = 'Cancelled'
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send cancellation email
        from email_service import send_status_update_email
        send_status_update_email(appointment, old_status, 'Cancelled')
        
        flash('Appointment cancelled successfully.', 'success')
        return redirect(url_for('user_dashboard'))
    
    @app.route('/profile')
    @login_required
    def user_profile():
        """User profile page"""
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        # Get statistics
        total_appointments = Appointment.query.filter_by(user_id=user_id).count()
        completed_appointments = Appointment.query.filter_by(user_id=user_id, status='Completed').count()
        
        return render_template('user_profile.html', 
                             user=user, 
                             total_appointments=total_appointments,
                             completed_appointments=completed_appointments)
    
    @app.route('/profile/edit', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        """Edit user profile"""
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if request.method == 'POST':
            try:
                user.name = request.form['name']
                user.phone = request.form['phone']
                
                # Update password if provided
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')
                
                if current_password and new_password:
                    if not user.check_password(current_password):
                        flash('Current password is incorrect.', 'danger')
                        return render_template('edit_profile.html', user=user)
                    
                    if new_password != confirm_password:
                        flash('New passwords do not match.', 'danger')
                        return render_template('edit_profile.html', user=user)
                    
                    if len(new_password) < 6:
                        flash('Password must be at least 6 characters.', 'danger')
                        return render_template('edit_profile.html', user=user)
                    
                    user.set_password(new_password)
                
                db.session.commit()
                
                # Update session
                session['user_name'] = user.name
                
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('user_profile'))
                
            except Exception as e:
                db.session.rollback()
                print(f"Error updating profile: {str(e)}")
                flash('An error occurred. Please try again.', 'danger')
        
        return render_template('edit_profile.html', user=user)