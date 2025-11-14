# email_service.py - Hybrid version (works locally with Gmail, on Render with SendGrid)
import os
import logging

logger = logging.getLogger(__name__)

# Check if SendGrid API key is available
USE_SENDGRID = bool(os.environ.get('SENDGRID_API_KEY'))

if USE_SENDGRID:
    # Use SendGrid for production (Render)
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail as SendGridMail
    logger.info("📧 Using SendGrid API for emails (Production)")
    
    # Dummy mail object for compatibility
    class DummyMail:
        def init_app(self, app):
            pass
    mail = DummyMail()
    
else:
    # Use Flask-Mail for local development
    from flask_mail import Mail, Message
    logger.info("📧 Using Gmail SMTP for emails (Local Development)")
    mail = Mail()


def init_mail(app):
    """Initialize email service"""
    if USE_SENDGRID:
        logger.info("✅ SendGrid API initialized")
    else:
        # Initialize Flask-Mail for local development
        app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
        app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
        app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@mentalhealth.com')
        mail.init_app(app)
        logger.info("✅ Flask-Mail (Gmail SMTP) initialized")


def send_appointment_confirmation(appointment):
    """Send appointment confirmation email"""
    
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
                    <p><strong>Appointment ID:</strong> #{appointment.id}</p>
                    <p><strong>Professional:</strong> {appointment.professional.name}</p>
                    <p><strong>Title:</strong> {appointment.professional.title}</p>
                    <p><strong>Service:</strong> {appointment.service}</p>
                    <p><strong>Date:</strong> {appointment.date.strftime('%B %d, %Y')}</p>
                    <p><strong>Time:</strong> {appointment.time.strftime('%I:%M %p')}</p>
                    <p><strong>Status:</strong> {appointment.status}</p>
                </div>
                
                <p><strong>What's Next?</strong></p>
                <ul>
                    <li>Your appointment is pending confirmation from our team</li>
                    <li>You will receive an update once it's confirmed</li>
                    <li>Please arrive 5-10 minutes before your scheduled time</li>
                </ul>
                
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
        print(f"📧 Sending confirmation email to {appointment.user_email}")
        
        if USE_SENDGRID:
            # Send via SendGrid API
            message = SendGridMail(
                from_email=os.environ.get('MAIL_DEFAULT_SENDER', 'codecrunch025@gmail.com'),
                to_emails=appointment.user_email,
                subject=subject,
                html_content=html_body
            )
            
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message)
            print(f"✅ Email sent via SendGrid! Status: {response.status_code}")
            
        else:
            # Send via Flask-Mail (Gmail SMTP)
            msg = Message(subject, recipients=[appointment.user_email])
            msg.html = html_body
            mail.send(msg)
            print(f"✅ Email sent via Gmail SMTP!")
        
        appointment.confirmation_sent = True
        return True
        
    except Exception as e:
        print(f"❌ Error sending confirmation email: {str(e)}")
        logger.error(f"Error sending confirmation email: {str(e)}")
        return False


def send_status_update_email(appointment, old_status, new_status):
    """Send email when appointment status changes"""
    
    subject = f"Appointment Status Update - #{appointment.id}"
    
    status_messages = {
        'Confirmed': {'title': '✅ Appointment Confirmed', 'message': 'Great news! Your appointment has been confirmed.', 'color': '#27ae60'},
        'Cancelled': {'title': '❌ Appointment Cancelled', 'message': 'Your appointment has been cancelled.', 'color': '#e74c3c'},
        'Completed': {'title': '🎉 Appointment Completed', 'message': 'Thank you for your session!', 'color': '#3498db'}
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
        if USE_SENDGRID:
            message = SendGridMail(
                from_email=os.environ.get('MAIL_DEFAULT_SENDER', 'codecrunch025@gmail.com'),
                to_emails=appointment.user_email,
                subject=subject,
                html_content=html_body
            )
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            sg.send(message)
        else:
            msg = Message(subject, recipients=[appointment.user_email])
            msg.html = html_body
            mail.send(msg)
        
        print(f"✅ Status update email sent to {appointment.user_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending status update email: {str(e)}")
        return False


def send_review_request_email(appointment):
    """Send email requesting review after completed appointment"""
    
    subject = f"How was your session? Leave a review"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #d4a574, #c8956d); color: white; padding: 30px; text-align: center; }}
            .content {{ background: #f9f9f9; padding: 30px; }}
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
                <p>Your feedback is valuable and helps others find the right professional.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        if USE_SENDGRID:
            message = SendGridMail(
                from_email=os.environ.get('MAIL_DEFAULT_SENDER', 'codecrunch025@gmail.com'),
                to_emails=appointment.user_email,
                subject=subject,
                html_content=html_body
            )
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            sg.send(message)
        else:
            msg = Message(subject, recipients=[appointment.user_email])
            msg.html = html_body
            mail.send(msg)
        
        return True
    except Exception as e:
        logger.error(f"Error sending review request email: {str(e)}")
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
            .header {{ background: linear-gradient(135deg, #d4a574, #c8956d); color: white; padding: 30px; text-align: center; }}
            .content {{ background: #f9f9f9; padding: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✉️ Message Received!</h1>
            </div>
            <div class="content">
                <p>Dear {contact.name},</p>
                <p>We've received your message and will respond within 24-48 hours.</p>
                <p><strong>Message ID:</strong> #{contact.id}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        if USE_SENDGRID:
            message = SendGridMail(
                from_email=os.environ.get('MAIL_DEFAULT_SENDER', 'codecrunch025@gmail.com'),
                to_emails=contact.email,
                subject=subject,
                html_content=html_body
            )
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            sg.send(message)
        else:
            msg = Message(subject, recipients=[contact.email])
            msg.html = html_body
            mail.send(msg)
        
        return True
    except Exception as e:
        logger.error(f"Error sending contact confirmation email: {str(e)}")
        return False


def send_appointment_reminder(appointment):
    """Send appointment reminder email (24 hours before)"""
    
    subject = f"Reminder: Upcoming Appointment Tomorrow - #{appointment.id}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #3498db, #2980b9); color: white; padding: 30px; text-align: center; }}
            .content {{ background: #f9f9f9; padding: 30px; }}
            .reminder-box {{ background: #fff3cd; padding: 20px; margin: 20px 0; border-radius: 8px; }}
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
                <div class="reminder-box">
                    <h3>Tomorrow's Appointment</h3>
                    <p><strong>Professional:</strong> {appointment.professional.name}</p>
                    <p><strong>Date:</strong> {appointment.date.strftime('%B %d, %Y')}</p>
                    <p><strong>Time:</strong> {appointment.time.strftime('%I:%M %p')}</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        if USE_SENDGRID:
            message = SendGridMail(
                from_email=os.environ.get('MAIL_DEFAULT_SENDER', 'codecrunch025@gmail.com'),
                to_emails=appointment.user_email,
                subject=subject,
                html_content=html_body
            )
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            sg.send(message)
        else:
            msg = Message(subject, recipients=[appointment.user_email])
            msg.html = html_body
            mail.send(msg)
        
        appointment.reminder_sent = True
        return True
    except Exception as e:
        logger.error(f"Error sending reminder email: {str(e)}")
        return False