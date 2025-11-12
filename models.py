# models.py - Enhanced database models
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """User model for patient accounts"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Professional(db.Model):
    """Professional model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text, nullable=False)
    experience_years = db.Column(db.Integer, nullable=False)
    education = db.Column(db.Text, nullable=False)
    languages = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200), default='default-avatar.jpg')
    available_days = db.Column(db.String(200), nullable=False)
    
    # Pricing
    consultation_fee = db.Column(db.Float, default=0.0)
    session_duration = db.Column(db.Integer, default=60)  # in minutes
    
    # Rating
    rating = db.Column(db.Float, default=5.0)
    total_reviews = db.Column(db.Integer, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='professional', lazy=True)
    reviews = db.relationship('Review', backref='professional', lazy=True)
    time_slots = db.relationship('TimeSlot', backref='professional', lazy=True, cascade='all, delete-orphan')
    
    def update_rating(self):
        """Recalculate average rating from reviews"""
        reviews = Review.query.filter_by(professional_id=self.id).all()
        if reviews:
            self.rating = sum(r.rating for r in reviews) / len(reviews)
            self.total_reviews = len(reviews)
        else:
            self.rating = 5.0
            self.total_reviews = 0
    
    def __repr__(self):
        return f'<Professional {self.name}>'

class Appointment(db.Model):
    """Appointment model"""
    id = db.Column(db.Integer, primary_key=True)
    
    # User info (can be guest or registered user)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(120), nullable=False)
    user_phone = db.Column(db.String(20), nullable=False)
    
    # Appointment details
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.Integer, default=60)  # in minutes
    message = db.Column(db.Text, nullable=True)
    
    # Status tracking
    status = db.Column(db.String(20), default='Pending')  # Pending, Confirmed, Completed, Cancelled
    
    # Payment
    payment_status = db.Column(db.String(20), default='Unpaid')  # Unpaid, Paid, Refunded
    amount = db.Column(db.Float, default=0.0)
    
    # Notifications
    confirmation_sent = db.Column(db.Boolean, default=False)
    reminder_sent = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    review = db.relationship('Review', backref='appointment', uselist=False, lazy=True)
    
    def __repr__(self):
        return f'<Appointment {self.user_name} - {self.date} {self.time}>'

class Review(db.Model):
    """Review and rating model"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    
    # Review details
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    
    # Moderation
    is_approved = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Review {self.rating} stars for Professional {self.professional_id}>'

class TimeSlot(db.Model):
    """Available time slots for professionals"""
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=False)
    
    # Day of week (0=Monday, 6=Sunday)
    day_of_week = db.Column(db.Integer, nullable=False)
    
    # Time range
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Status
    is_available = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<TimeSlot {self.day_of_week} {self.start_time}-{self.end_time}>'

class Notification(db.Model):
    """Notification log for tracking sent emails/SMS"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Recipient
    user_email = db.Column(db.String(120), nullable=False)
    user_phone = db.Column(db.String(20), nullable=True)
    
    # Notification details
    notification_type = db.Column(db.String(50), nullable=False)  # confirmation, reminder, cancellation
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=True)
    
    # Content
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='Pending')  # Pending, Sent, Failed
    sent_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.notification_type} to {self.user_email}>'
    
class Contact(db.Model):
    """Contact/Support message model"""
    id = db.Column(db.Integer, primary_key=True)
    
    # User info
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='Unread')  # Unread, Read, Resolved
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Contact {self.name} - {self.subject}>'