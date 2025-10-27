# review_routes.py - Review and rating system routes
from flask import render_template, request, redirect, url_for, flash, session
from models import db, Review, Appointment, Professional, User
from datetime import datetime

def add_review_routes(app):
    """Add review routes to the Flask app"""
    
    @app.route('/leave-review/<int:appt_id>', methods=['GET', 'POST'])
    def leave_review(appt_id):
        """Leave a review for a completed appointment"""
        appointment = Appointment.query.get_or_404(appt_id)
        
        # Check if appointment is completed
        if appointment.status != 'Completed':
            flash('You can only review completed appointments.', 'warning')
            return redirect(url_for('index'))
        
        # Check if review already exists
        existing_review = Review.query.filter_by(appointment_id=appt_id).first()
        if existing_review:
            flash('You have already reviewed this appointment.', 'info')
            return redirect(url_for('professional_detail', prof_id=appointment.professional_id))
        
        if request.method == 'POST':
            try:
                rating = int(request.form['rating'])
                comment = request.form.get('comment', '').strip()
                is_anonymous = 'is_anonymous' in request.form
                
                # Validation
                if rating < 1 or rating > 5:
                    flash('Please provide a rating between 1 and 5 stars.', 'danger')
                    return render_template('leave_review.html', appointment=appointment)
                
                # Create review
                review = Review(
                    user_id=appointment.user_id,
                    professional_id=appointment.professional_id,
                    appointment_id=appointment.id,
                    rating=rating,
                    comment=comment if comment else None,
                    is_anonymous=is_anonymous,
                    is_approved=True  # Auto-approve for now, add moderation later
                )
                
                db.session.add(review)
                
                # Update professional's rating
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
    
    @app.route('/professional/<int:prof_id>/reviews')
    def professional_reviews(prof_id):
        """View all reviews for a professional"""
        professional = Professional.query.get_or_404(prof_id)
        
        # Get approved reviews
        reviews = Review.query.filter_by(
            professional_id=prof_id,
            is_approved=True
        ).order_by(Review.created_at.desc()).all()
        
        # Calculate rating distribution
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            rating_counts[review.rating] += 1
        
        return render_template('professional_reviews.html', 
                             professional=professional,
                             reviews=reviews,
                             rating_counts=rating_counts)
    
    @app.route('/admin/reviews')
    def admin_reviews():
        """Admin page to moderate reviews"""
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        
        # Get all reviews
        reviews = Review.query.order_by(Review.created_at.desc()).all()
        
        return render_template('admin_reviews.html', reviews=reviews)
    
    @app.route('/admin/review/<int:review_id>/approve', methods=['POST'])
    def approve_review(review_id):
        """Approve a review"""
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        
        try:
            review = Review.query.get_or_404(review_id)
            review.is_approved = True
            
            # Update professional rating
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
            
            # Update professional rating
            professional = Professional.query.get(professional_id)
            professional.update_rating()
            
            db.session.commit()
            
            flash('Review deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting review: {str(e)}")
            flash('An error occurred.', 'danger')
        
        return redirect(url_for('admin_reviews'))