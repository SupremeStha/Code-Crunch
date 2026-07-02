# Code Crunch — Mental Health Booking Platform

A full-stack web application that connects users with mental health professionals. It combines a traditional appointment booking workflow with an AI-assisted chatbot that guides users through conversational triage and booking, along with review management, email notifications, and an admin dashboard.

## Features

### For Users
- Account registration and secure login (password hashing via Werkzeug)
- Browse mental health professionals with specialization, experience, ratings, and availability
- AI chatbot for guided, conversational appointment booking with built-in crisis-resource handling
- Direct appointment booking through a professional's profile
- Personal dashboard to view upcoming and past appointments
- Appointment cancellation (with a 24-hour advance notice policy)
- Leave ratings and reviews for completed appointments
- Check appointment status without logging in, via email lookup

### For Admins
- Admin login and dedicated dashboard
- Manage professional profiles (add, edit, delete)
- View and manage all appointments, including status updates
- Moderate reviews (approve or reject)
- Automatic professional rating recalculation as reviews are approved or removed

### System Features
- Automated email notifications: booking confirmations, status updates, review requests, and appointment reminders
- Session-based chatbot state, with support for loading conversation history back into a session
- Crisis alert tracking within chatbot conversations
- Health check endpoint for uptime monitoring

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLAlchemy ORM with SQLite
- **Authentication:** Flask sessions, Werkzeug password hashing
- **Email:** Flask-Mail (see `email_service.py`)
- **Frontend:** HTML, CSS, JavaScript, Jinja2 templates
- **Environment Management:** python-dotenv

## Project Structure

```
Code-Crunch/
├── app.py                 # Main application, routes, and view logic
├── models.py               # SQLAlchemy models (User, Professional, Appointment, Review, Contact)
├── chatbot.py               # MentalHealthChatbot — conversational triage and booking logic
├── email_service.py         # Email notification functions
├── contact_routes.py        # Contact form routes
├── review_routes.py         # Review-related routes
├── auth_routes.py           # Authentication-related routes
├── safety.py                 # Crisis detection / safety logic for the chatbot
├── templates/                # Jinja2 HTML templates (including admin/ subfolder)
├── static/                   # CSS, JS, and image assets
└── requirements.txt          # Python dependencies
```

*(Structure inferred from the codebase — adjust filenames above if your repo differs.)*

## Getting Started

### Prerequisites
- Python 3.9+
- pip

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/SupremeStha/Code-Crunch.git
   cd Code-Crunch
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables

   Create a `.env` file in the project root (do not commit this file):
   ```
   SECRET_KEY=your-secret-key-here
   MAIL_SERVER=smtp.example.com
   MAIL_PORT=587
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-email-password
   ```

5. Run the application
   ```bash
   python app.py
   ```

   The app will be available at `http://localhost:5000`.

## Admin Access

Admin login is available at `/admin/login`. **Before deploying this project or sharing it publicly, replace the default admin credentials in `app.py` with values loaded from environment variables** rather than hardcoded strings.

## Security Notes

This project was built as a learning exercise. If you plan to deploy it or share the repository publicly, consider addressing the following:
- Move admin credentials out of source code and into environment variables
- Ensure `.env` is listed in `.gitignore` and is not committed to version control
- Rotate any credentials that may have previously been committed
- Add CSRF protection to form submissions
- Add rate limiting to login and admin login routes

## License

This project is available for educational and portfolio purposes. Add a license of your choice (e.g., MIT) if you plan to open it up for reuse or contributions.
