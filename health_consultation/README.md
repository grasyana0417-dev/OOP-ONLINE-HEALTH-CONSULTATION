# Barangay Guimbala Online Health Consultation System

A comprehensive Django-based web application for online health consultation services in Barangay Guimbala, Silay City, Philippines.

## Features

### Core Features

1. **Landing Page**
   - Modern, aesthetic design with forest green theme
   - Service overview and feature highlights
   - Consultation types showcase
   - How it works guide
   - Call-to-action sections

2. **User Authentication & Roles**
   - Custom user model with email-based login
   - Three user roles:
     - **Resident**: Can book appointments, chat, view records
     - **Barangay Health Worker/Midwife**: Manage appointments, conduct consultations
     - **Admin**: System management and user oversight
   - Role-based dashboard redirection

3. **Appointment Scheduling**
   - Book appointments with health workers
   - Multiple consultation types:
     - Prenatal Care
     - Child Health
     - General Health Concern
     - Family Planning
     - Follow-up Checkup
     - Immunization
     - Nutrition Counseling
     - Dental Checkup
     - Mental Health
   - Online and in-person consultation options
   - Appointment status tracking (Pending, Approved, Rescheduled, Completed, Cancelled)

4. **Online Consultation**
   - Video/Voice call interface
   - Real-time chat during consultation
   - Call quality tracking
   - Consultation notes and records

5. **Real-Time Chat**
   - Messaging between residents and health workers
   - Chat history preservation
   - File attachment support
   - Message read receipts
   - Notification system integration

6. **Notifications**
   - In-app notifications for:
     - Appointment requests
     - Appointment approvals
     - Rescheduling
     - Cancellations
     - New messages
   - Notification preferences
   - Unread count badges

7. **Consultation Records**
   - Complete consultation history
   - Medical notes and recommendations
   - Vital signs tracking
   - Follow-up scheduling
   - Downloadable records

8. **Admin Dashboard**
   - User management
   - Appointment monitoring
   - System statistics
   - Consultation reports

## Technology Stack

- **Backend**: Python Django 4.2+
- **Database**: SQLite (default), PostgreSQL/MySQL compatible
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Authentication**: Django built-in authentication
- **Real-time**: Django Channels (WebSocket)
- **Styling**: Custom CSS (No Bootstrap/Tailwind)

## Color Scheme

- **Primary**: Lush Forest Green (#1a5f4a)
- **Primary Dark**: Deep Forest (#0d3b2e)
- **Primary Light**: Soft Green (#2d7a5f)
- **Background**: White (#ffffff)
- **Accent**: Light Mint (#f0f9f6)
- **Text**: Dark Gray (#2d3a35)

## Project Structure

```
health_consultation/
├── health_consultation/          # Main project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                      # User management
│   ├── models.py                 # Custom User model, Profiles
│   ├── views.py                  # Authentication views
│   ├── forms.py                  # Registration/Login forms
│   └── templates/                # Auth templates
├── appointments/                # Appointment scheduling
│   ├── models.py                 # Appointment, ConsultationRecord
│   ├── views.py                  # CRUD operations
│   └── forms.py                  # Appointment forms
├── chat/                        # Real-time messaging
│   ├── models.py                 # ChatMessage, ChatRoom
│   ├── views.py                  # Chat interface
│   ├── consumers.py              # WebSocket consumers
│   └── routing.py                # WebSocket routing
├── consultations/               # Online call management
│   ├── models.py                 # OnlineConsultation
│   ├── views.py                  # Call room interface
│   └── forms.py                  # Feedback forms
├── notifications/               # Notification system
│   ├── models.py                 # Notification model
│   ├── utils.py                  # Notification helpers
│   └── context_processors.py     # Unread count
├── templates/                   # Global templates
│   ├── base.html
│   ├── landing.html
│   └── includes/
├── static/                      # Static files
│   ├── css/                     # Stylesheets
│   │   ├── style.css            # Main styles
│   │   ├── animations.css       # Animations
│   │   └── responsive.css       # Responsive design
│   └── js/                      # JavaScript
│       ├── main.js              # Core functionality
│       └── animations.js        # Animation effects
├── media/                       # User uploads
├── db.sqlite3                   # SQLite database
└── manage.py                    # Django management
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Step-by-Step Setup

1. **Clone or create the project directory**
   ```bash
   mkdir health_consultation
   cd health_consultation
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser (admin)**
   ```bash
   python manage.py createsuperuser
   # Enter email, first name, last name, and password
   # Set role to 'admin' when prompted
   ```

6. **Create sample data (optional)**
   ```bash
   python manage.py shell
   ```
   ```python
   from accounts.models import User
   
   # Create a health worker
   worker = User.objects.create_user(
       email='worker@guimbala.health',
       password='testpass123',
       first_name='Maria',
       last_name='Santos',
       role='health_worker',
       phone_number='0917-123-4567'
   )
   
   # Create a resident
   resident = User.objects.create_user(
       email='resident@example.com',
       password='testpass123',
       first_name='Juan',
       last_name='Dela Cruz',
       role='resident',
       phone_number='0918-987-6543',
       address='Barangay Guimbala, Silay City'
   )
   
   # Create resident profile
   from accounts.models import ResidentProfile
   ResidentProfile.objects.create(
       user=resident,
       age=35,
       gender='male'
   )
   
   exit()
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open browser: `http://127.0.0.1:8000/`
   - Admin panel: `http://127.0.0.1:8000/admin/`

## Usage

### For Residents

1. **Register**: Create an account at `/accounts/register/`
2. **Book Appointment**: Navigate to dashboard and click "Book Appointment"
3. **Chat**: Access chat interface to message health workers
4. **View Records**: Check consultation history in records section

### For Health Workers

1. **Login**: Use credentials provided by admin
2. **Manage Availability**: Toggle availability status on dashboard
3. **Review Appointments**: Check pending requests and approve/decline
4. **Conduct Consultations**: Join online calls or chat with residents
5. **Add Notes**: Complete consultation records after sessions

### For Administrators

1. **Access Admin**: Login at `/admin/` with superuser credentials
2. **Manage Users**: Add/edit users, assign roles
3. **Monitor System**: View all appointments and consultations
4. **Generate Reports**: Export consultation data

## Key URLs

- Home: `/`
- Login: `/accounts/login/`
- Register: `/accounts/register/`
- Dashboard: `/accounts/dashboard/`
- Appointments: `/appointments/`
- Chat: `/chat/`
- Admin: `/admin/`

## Features in Detail

### Animations Included

- Page loading animation with health pulse icon
- Fade-in on scroll for content sections
- Card hover lift effects
- Button scale animations
- Smooth page transitions
- Notification badge pulse
- Chat message entrance animations
- Call status pulse animation
- Staggered element animations

### Responsive Design

- Mobile-first approach
- Breakpoints: 480px, 768px, 1024px, 1400px
- Hamburger menu for mobile
- Touch-friendly interface
- Accessible on all devices

### Security Features

- CSRF protection
- Secure password handling
- Role-based access control
- Session management
- XSS prevention

## Customization

### Changing Colors

Edit `static/css/style.css` and modify CSS variables:

```css
:root {
    --primary: #your-color;
    --primary-dark: #your-dark-color;
    /* ... */
}
```

### Adding New Consultation Types

Edit `appointments/models.py` and add to `CONSULTATION_TYPE_CHOICES`:

```python
CONSULTATION_TYPE_CHOICES = [
    # existing types...
    ('new_type', 'New Type Display Name'),
]
```

### Email Configuration

Edit `health_consultation/settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

### Jitsi as a Service (8x8.vc) Configuration

Set environment variables before running the server:

```bash
# Windows PowerShell
$env:JITSI_DOMAIN="8x8.vc"
$env:JITSI_APP_ID="vpaas-magic-cookie-b76a76dae6204bacb9bddce34394ecbe"
# Optional testing token (expires): 
# $env:JITSI_JWT="<your-jaas-jwt>"
```

```bash
# macOS/Linux
export JITSI_DOMAIN="8x8.vc"
export JITSI_APP_ID="vpaas-magic-cookie-b76a76dae6204bacb9bddce34394ecbe"
# Optional testing token (expires):
# export JITSI_JWT="<your-jaas-jwt>"
```

Notes:
- Room format is automatically handled as `<APP_ID>/<room_id>` when `JITSI_APP_ID` is set.
- Do not commit JWT/private keys to source control.

## Deployment

### Production Checklist

1. Set `DEBUG = False` in settings.py
2. Configure proper `ALLOWED_HOSTS`
3. Use PostgreSQL or MySQL database
4. Set up static files serving (WhiteNoise or CDN)
5. Configure SSL/HTTPS
6. Set up environment variables for secrets
7. Configure logging

### Using WhiteNoise for Static Files

```bash
pip install whitenoise
```

Add to `settings.py`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... other middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

## Support

For issues or questions:
- Contact: Barangay Guimbala Health Center
- Location: Silay City, Negros Occidental, Philippines
- Email: health@guimbala-silay.gov.ph

## License

This project is developed for Barangay Guimbala, Silay City, Philippines.

## Credits

- System Design & Development: Barangay Guimbala IT Team
- Health Content: Barangay Health Workers & Midwives
- UI/UX: Modern Healthcare Design Standards

---

**Note**: This system is designed specifically for Barangay Guimbala's health consultation needs and follows Philippine health service standards.
