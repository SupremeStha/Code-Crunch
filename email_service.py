# email_service.py - Email notification system (FIXED FOR RENDER)
from flask_mail import Mail, Message
from flask import render_template_string
from datetime import datetime, timedelta
import os

mail = Mail()

def get_base_url():
    """Get base URL from environment or default to localhost"""
    return os.environ.get('APP_URL', 'http://localhost:5000')

def init_mail(app):
    """Initialize Flask-Mail with app config"""
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@mentalhealth.com')
    
    # CRITICAL: Add timeout settings to prevent 502 errors
    app.config['MAIL_MAX_EMAILS'] = None
    app.config['MAIL_TIMEOUT'] = 10  # 10 second timeout
    
    mail.init_app(app)

def send_appointment_confirmation(appointment):
    """Send appointment confirmation email"""
    base_url = get_base_url()
    subject = f"Appointment Confirmation - #{appointment.id}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #d4a574, #c8956d); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .detail-box {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #c8956d; }}
            .detail-row {{ display: flex; padding: 10px 0; border-bottom: 1px solid #eee; }}
            .detail-label {{ font-weight: bold; width: 150px; color: #666; }}
            .detail-value {{ color: #2c3e50; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #d4a574, #c8956d); color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Appointment Confirmed!</h1>
                <p>Your appointment has been successfully scheduled</p>
            </div>
            <div class="content">
                <p>Dear {appointment.user_name},</p>
                <p>Thank you for booking an appointment with us. Here are your appointment details:</p>
                
                <div class="detail-box">
                    <h3 style="margin-top: 0; color: #c8956d;">Appointment Details</h3>
                    <div class="detail-row">
                        <span class="detail-label">Appointment ID:</span>
                        <span class="detail-value">#{appointment.id}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Professional:</span>
                        <span class="detail-value">{appointment.professional.name}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Title:</span>
                        <span class="detail-value">{appointment.professional.title}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Service:</span>
                        <span class="detail-value">{appointment.service}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Date:</span>
                        <span class="detail-value">{appointment.date.strftime('%B %d, %Y')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Time:</span>
                        <span class="detail-value">{appointment.time.strftime('%I:%M %p')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Status:</span>
                        <span class="detail-value" style="color: #f39c12; font-weight: bold;">{appointment.status}</span>
                    </div>
                </div>
                
                <p><strong>What's Next?</strong></p>
                <ul>
                    <li>Your appointment is pending confirmation from our team</li>
                    <li>You will receive an update once it's confirmed</li>
                    <li>Please arrive 5-10 minutes before your scheduled time</li>
                </ul>
                
                <center>
                    <a href="{base_url}/check-status" class="button">Check Appointment Status</a>
                </center>
                
                <p>If you need to cancel or reschedule, please contact us at least 24 hours in advance.</p>
                
                <div class="footer">
                    <p>Mental Health Platform | © 2025 All Rights Reserved</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = Message(subject, recipients=[appointment.user_email])
        msg.html = html_body
        mail.send(msg)
        
        # Mark as sent
        appointment.confirmation_sent = True
        
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {str(e)}")
        return False

def send_appointment_reminder(appointment):
    """Send appointment reminder email (24 hours before)"""
    base_url = get_base_url()
    subject = f"Reminder: Upcoming Appointment Tomorrow - #{appointment.id}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #3498db, #2980b9); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .reminder-box {{ background: #fff3cd; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #ffc107; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #d4a574, #c8956d); color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⏰ Appointment Reminder</h1>
                <p>Your appointment is tomorrow!</p>
            </div>
            <div class="content">
                <p>Dear {appointment.user_name},</p>
                <p>This is a friendly reminder about your upcoming appointment.</p>
                
                <div class="reminder-box">
                    <h3 style="margin-top: 0;">Tomorrow's Appointment</h3>
                    <p><strong>Professional:</strong> {appointment.professional.name}</p>
                    <p><strong>Date:</strong> {appointment.date.strftime('%B %d, %Y')}</p>
                    <p><strong>Time:</strong> {appointment.time.strftime('%I:%M %p')}</p>
                    <p><strong>Service:</strong> {appointment.service}</p>
                </div>
                
                <p><strong>Important Reminders:</strong></p>
                <ul>
                    <li>Please arrive 5-10 minutes early</li>
                    <li>Bring any relevant documents or medical records</li>
                    <li>Prepare any questions you'd like to discuss</li>
                </ul>
                
                <center>
                    <a href="{base_url}/check-status" class="button">View Appointment Details</a>
                </center>
                
                <p>If you need to cancel, please let us know as soon as possible.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = Message(subject, recipients=[appointment.user_email])
        msg.html = html_body
        mail.send(msg)
        
        # Mark as sent
        appointment.reminder_sent = True
        
        return True
    except Exception as e:
        print(f"Error sending reminder email: {str(e)}")
        return False

def send_status_update_email(appointment, old_status, new_status):
    """Send email when appointment status changes"""
    subject = f"Appointment Status Update - #{appointment.id}"
    
    status_messages = {
        'Confirmed': {
            'title': '✅ Appointment Confirmed',
            'message': 'Great news! Your appointment has been confirmed.',
            'color': '#27ae60'
        },
        'Cancelled': {
            'title': '❌ Appointment Cancelled',
            'message': 'Your appointment has been cancelled.',
            'color': '#e74c3c'
        },
        'Completed': {
            'title': '🎉 Appointment Completed',
            'message': 'Thank you for your session! We hope it was helpful.',
            'color': '#3498db'
        }
    }
    
    status_info = status_messages.get(new_status, {
        'title': 'Appointment Status Updated',
        'message': f'Your appointment status has been updated to {new_status}.',
        'color': '#f39c12'
    })
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: {status_info['color']}; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{status_info['title']}</h1>
                <p>{status_info['message']}</p>
            </div>
            <div class="content">
                <p>Dear {appointment.user_name},</p>
                <p>Your appointment (ID: #{appointment.id}) status has been updated:</p>
                <p><strong>Previous Status:</strong> {old_status}</p>
                <p><strong>New Status:</strong> {new_status}</p>
                <p><strong>Date:</strong> {appointment.date.strftime('%B %d, %Y')} at {appointment.time.strftime('%I:%M %p')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = Message(subject, recipients=[appointment.user_email])
        msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending status update email: {str(e)}")
        return False

def send_review_request_email(appointment):
    """Send email requesting review after completed appointment"""
    base_url = get_base_url()
    subject = f"How was your session? Leave a review"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #d4a574, #c8956d); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .stars {{ font-size: 30px; text-align: center; margin: 20px 0; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #d4a574, #c8956d); color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⭐ Share Your Experience</h1>
                <p>How was your session with {appointment.professional.name}?</p>
            </div>
            <div class="content">
                <p>Dear {appointment.user_name},</p>
                <p>Thank you for choosing our mental health services. We hope your session was helpful!</p>
                <p>Your feedback is valuable and helps others find the right professional for their needs.</p>
                
                <center>
                    <a href="{base_url}/leave-review/{appointment.id}" class="button">Leave a Review</a>
                </center>
                
                <p>It only takes a minute and makes a big difference!</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = Message(subject, recipients=[appointment.user_email])
        msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending review request email: {str(e)}")
        return False
    
def send_contact_confirmation(contact):
    """Send confirmation email when user submits contact form"""
    subject = "We've received your message"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #d4a574, #c8956d); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .message-box {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #c8956d; }}
            .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✉️ Message Received!</h1>
                <p>Thank you for contacting us</p>
            </div>
            <div class="content">
                <p>Dear {contact.name},</p>
                <p>We've received your message and our team will review it shortly. We typically respond within 24-48 hours.</p>
                
                <div class="message-box">
                    <h3 style="margin-top: 0; color: #c8956d;">Your Message Details</h3>
                    <p><strong>Subject:</strong> {contact.subject}</p>
                    <p><strong>Message ID:</strong> #{contact.id}</p>
                    <p><strong>Submitted:</strong> {contact.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <p><strong>What happens next?</strong></p>
                <ul>
                    <li>Our support team will review your message</li>
                    <li>We'll respond to your email address: {contact.email}</li>
                    <li>You can reference Message ID #{contact.id} in any follow-up communication</li>
                </ul>
                
                <p>If your matter is urgent, please call us directly during business hours.</p>
                
                <div class="footer">
                    <p>Mental Health Platform | © 2025 All Rights Reserved</p>
                    <p>This is an automated confirmation. Please do not reply to this email.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = Message(subject, recipients=[contact.email])
        msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending contact confirmation email: {str(e)}")
        return False