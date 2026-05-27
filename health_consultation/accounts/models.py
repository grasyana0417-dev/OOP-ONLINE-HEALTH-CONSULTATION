from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model for Barangay Guimbala Health Consultation System.
    Uses email as the primary identifier instead of username.
    """
    
    ROLE_CHOICES = [
        ('resident', 'Resident'),
        ('health_worker', 'Barangay Health Worker/Midwife'),
        ('admin', 'Admin'),
    ]
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='resident')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Health Worker specific fields
    license_number = models.CharField(max_length=50, blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    @property
    def is_resident(self):
        return self.role == 'resident'
    
    @property
    def is_health_worker(self):
        return self.role == 'health_worker'
    
    @property
    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser
    
    def get_dashboard_url(self):
        if self.is_admin_user:
            return reverse('accounts:admin_dashboard')
        elif self.is_health_worker:
            return reverse('accounts:worker_dashboard')
        else:
            return reverse('accounts:resident_dashboard')


class ResidentProfile(models.Model):
    """Extended profile information for residents."""
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    CIVIL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('widowed', 'Widowed'),
        ('separated', 'Separated'),
        ('divorced', 'Divorced'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resident_profile')
    age = models.PositiveIntegerField(blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS_CHOICES, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True, help_text="Brief medical history or conditions")
    allergies = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Resident Profile'
        verbose_name_plural = 'Resident Profiles'
    
    def __str__(self):
        return f"Profile: {self.user.get_full_name()}"


class HealthWorkerProfile(models.Model):
    """Extended profile information for Barangay Health Workers/Midwives."""
    
    SPECIALIZATION_CHOICES = [
        ('general', 'General Health'),
        ('prenatal', 'Prenatal Care'),
        ('child_health', 'Child Health'),
        ('family_planning', 'Family Planning'),
        ('midwifery', 'Midwifery'),
        ('nutrition', 'Nutrition'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='health_worker_profile')
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES, default='general')
    years_of_experience = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True, null=True)
    schedule_start = models.TimeField(default='08:00')
    schedule_end = models.TimeField(default='17:00')
    days_available = models.CharField(max_length=50, default='Mon,Tue,Wed,Thu,Fri', 
                                       help_text="Comma-separated days (Mon,Tue,Wed,Thu,Fri)")
    is_on_duty = models.BooleanField(default=False)
    consultation_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Health Worker Profile'
        verbose_name_plural = 'Health Worker Profiles'
    
    def __str__(self):
        return f"Health Worker: {self.user.get_full_name()}"
    
    def increment_consultation_count(self):
        self.consultation_count += 1
        self.save()
