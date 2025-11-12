# contact_routes.py - Contact Us functionality
from flask import render_template, request, redirect, url_for, flash, session
from datetime import datetime

def add_contact_routes(app):
    """Add contact routes to the Flask app"""
    
    # Import inside function to avoid circular imports
    from models import db, Contact
    from email_service import send_contact_confirmation
    
    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        """Contact us page"""
        if request.method == 'POST':
            try:
                name = request.form['name']
                email = request.form['email']
                phone = request.form.get('phone', '')
                subject = request.form['subject']
                message = request.form['message']
                
                # Validation
                if not all([name, email, subject, message]):
                    flash('Please fill in all required fields.', 'danger')
                    return render_template('contact.html')
                
                # Create contact message
                contact_msg = Contact(
                    name=name,
                    email=email,
                    phone=phone if phone else None,
                    subject=subject,
                    message=message,
                    status='Unread'
                )
                
                db.session.add(contact_msg)
                db.session.commit()
                
                # Send confirmation email
                try:
                    send_contact_confirmation(contact_msg)
                except Exception as e:
                    print(f"Error sending confirmation email: {str(e)}")
                
                flash('Thank you for contacting us! We\'ll get back to you within 24-48 hours.', 'success')
                return redirect(url_for('contact_success', msg_id=contact_msg.id))
                
            except Exception as e:
                db.session.rollback()
                print(f"Error submitting contact form: {str(e)}")
                import traceback
                traceback.print_exc()
                flash('An error occurred. Please try again.', 'danger')
        
        return render_template('contact.html')
    
    @app.route('/contact/success/<int:msg_id>')
    def contact_success(msg_id):
        """Contact form success page"""
        from models import Contact
        contact_msg = Contact.query.get_or_404(msg_id)
        return render_template('contact_success.html', contact=contact_msg)
    
    @app.route('/admin/contacts')
    def admin_contacts():
        """Admin page to view all contact messages"""
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        
        from models import Contact
        
        # Get all contacts ordered by newest first
        contacts = Contact.query.order_by(Contact.created_at.desc()).all()
        
        # Count by status
        unread_count = Contact.query.filter_by(status='Unread').count()
        read_count = Contact.query.filter_by(status='Read').count()
        resolved_count = Contact.query.filter_by(status='Resolved').count()
        
        return render_template('admin/admin_contacts.html', 
                             contacts=contacts,
                             unread_count=unread_count,
                             read_count=read_count,
                             resolved_count=resolved_count)
    
    @app.route('/admin/contact/<int:msg_id>')
    def view_contact(msg_id):
        """View individual contact message"""
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        
        from models import Contact
        contact = Contact.query.get_or_404(msg_id)
        
        # Mark as read if it was unread
        if contact.status == 'Unread':
            contact.status = 'Read'
            contact.updated_at = datetime.utcnow()
            db.session.commit()
        
        return render_template('admin/view_contact.html', contact=contact)
    
    @app.route('/admin/contact/<int:msg_id>/update-status', methods=['POST'])
    def update_contact_status(msg_id):
        """Update contact message status"""
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        
        try:
            from models import Contact
            contact = Contact.query.get_or_404(msg_id)
            new_status = request.form['status']
            admin_notes = request.form.get('admin_notes', '')
            
            contact.status = new_status
            if admin_notes:
                contact.admin_notes = admin_notes
            contact.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Contact status updated to {new_status}', 'success')
            
        except Exception as e:
            db.session.rollback()
            print(f"Error updating contact status: {str(e)}")
            flash('Error updating status. Please try again.', 'danger')
        
        return redirect(url_for('view_contact', msg_id=msg_id))
    
    @app.route('/admin/contact/<int:msg_id>/delete')
    def delete_contact(msg_id):
        """Delete a contact message"""
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        
        try:
            from models import Contact
            contact = Contact.query.get_or_404(msg_id)
            db.session.delete(contact)
            db.session.commit()
            
            flash('Contact message deleted successfully', 'success')
            
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting contact: {str(e)}")
            flash('Error deleting contact. Please try again.', 'danger')
        
        return redirect(url_for('admin_contacts'))