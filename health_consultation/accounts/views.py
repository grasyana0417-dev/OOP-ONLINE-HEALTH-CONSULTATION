from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import User, ResidentProfile, HealthWorkerProfile
from appointments.models import Appointment
from chat.models import ChatMessage
from notifications.models import Notification
from .forms import (
    UserRegistrationForm, UserLoginForm, ProfileUpdateForm,
    ResidentProfileForm, HealthWorkerProfileForm, PasswordUpdateForm
)


def register_view(request):
    """View for resident registration."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('accounts:resident_login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """View for user login."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def resident_login_view(request):
    """Resident-styled login page (accepts all valid roles)."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(user.get_dashboard_url())
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login_resident.html', {'form': form})


def worker_login_view(request):
    """Health worker-styled login page (accepts all valid roles)."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(user.get_dashboard_url())
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login_worker.html', {'form': form})


def admin_login_view(request):
    """Admin-styled login page (accepts all valid roles)."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(user.get_dashboard_url())
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login_admin.html', {'form': form})


@login_required
def logout_view(request):
    """View for user logout."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def dashboard_redirect_view(request):
    """Redirect users to their appropriate dashboard based on role."""
    if request.user.is_admin_user:
        return redirect('accounts:admin_dashboard')
    elif request.user.is_health_worker:
        return redirect('accounts:worker_dashboard')
    else:
        return redirect('accounts:resident_dashboard')


@login_required
def resident_dashboard_view(request):
    """Dashboard view for residents."""
    if not request.user.is_resident:
        return redirect('accounts:dashboard_redirect')
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        resident=request.user,
        status__in=['pending', 'approved'],
        scheduled_date__gte=timezone.now().date()
    ).order_by('scheduled_date', 'scheduled_time')[:5]
    
    # Get consultation history count
    consultation_count = Appointment.objects.filter(
        resident=request.user,
        status='completed'
    ).count()
    
    # Get unread notifications count
    unread_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    # Get recent chat messages
    recent_messages = ChatMessage.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-created_at')[:5]
    
    context = {
        'upcoming_appointments': upcoming_appointments,
        'consultation_count': consultation_count,
        'unread_notifications': unread_notifications,
        'recent_messages': recent_messages,
        'user': request.user,
    }
    return render(request, 'accounts/resident_dashboard.html', context)


@login_required
def worker_dashboard_view(request):
    """Dashboard view for Barangay Health Workers/Midwives."""
    if not request.user.is_health_worker:
        return redirect('accounts:dashboard_redirect')
    
    # Get pending appointment requests
    pending_appointments = Appointment.objects.filter(
        Q(health_worker=request.user) | Q(health_worker__isnull=True),
        status='pending'
    ).order_by('scheduled_date', 'scheduled_time')[:10]
    
    # Get today's appointments
    today = timezone.now().date()
    today_appointments = Appointment.objects.filter(
        health_worker=request.user,
        scheduled_date=today,
        status='approved'
    ).order_by('scheduled_time')
    
    # Get statistics
    total_consultations = Appointment.objects.filter(
        health_worker=request.user,
        status='completed'
    ).count()
    
    weekly_appointments = Appointment.objects.filter(
        health_worker=request.user,
        scheduled_date__gte=today - timedelta(days=7)
    ).count()
    
    # Get unread messages from residents
    unread_messages = ChatMessage.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()
    
    context = {
        'pending_appointments': pending_appointments,
        'today_appointments': today_appointments,
        'total_consultations': total_consultations,
        'weekly_appointments': weekly_appointments,
        'unread_messages': unread_messages,
        'user': request.user,
    }
    return render(request, 'accounts/worker_dashboard.html', context)


@login_required
def admin_dashboard_view(request):
    """Dashboard view for Administrators."""
    if not request.user.is_admin_user:
        return redirect('accounts:dashboard_redirect')
    
    # Get system statistics
    total_residents = User.objects.filter(role='resident').count()
    total_workers = User.objects.filter(role='health_worker').count()
    total_appointments = Appointment.objects.count()
    
    today = timezone.now().date()
    todays_appointments = Appointment.objects.filter(
        scheduled_date=today
    ).count()
    
    # Get recent appointments
    recent_appointments = Appointment.objects.all().order_by('-created_at')[:10]
    
    # Get pending appointment requests
    pending_count = Appointment.objects.filter(status='pending').count()
    
    # Get consultation type distribution
    consultation_types = Appointment.objects.values('consultation_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'total_residents': total_residents,
        'total_workers': total_workers,
        'total_appointments': total_appointments,
        'todays_appointments': todays_appointments,
        'recent_appointments': recent_appointments,
        'pending_count': pending_count,
        'consultation_types': consultation_types,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
def profile_view(request):
    """View user profile."""
    user = request.user
    
    if user.is_resident:
        profile, created = ResidentProfile.objects.get_or_create(user=user)
        form_class = ResidentProfileForm
        template = 'accounts/resident_profile.html'
    elif user.is_health_worker:
        profile, created = HealthWorkerProfile.objects.get_or_create(user=user)
        form_class = HealthWorkerProfileForm
        template = 'accounts/worker_profile.html'
    else:
        profile = None
        form_class = None
        template = 'accounts/profile.html'
    
    if request.method == 'POST':
        user_form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        
        if form_class:
            profile_form = form_class(request.POST, instance=profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('accounts:profile')
        else:
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('accounts:profile')
    else:
        user_form = ProfileUpdateForm(instance=user)
        profile_form = form_class(instance=profile) if form_class else None
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user': user,
        'profile': profile,
    }
    return render(request, template, context)


@login_required
def change_password_view(request):
    """View for changing password."""
    if request.method == 'POST':
        form = PasswordUpdateForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordUpdateForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def toggle_availability_view(request):
    """Toggle health worker availability status."""
    if not request.user.is_health_worker:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        request.user.is_available = not request.user.is_available
        request.user.save()
        
        # Also update health worker profile
        try:
            profile = request.user.health_worker_profile
            profile.is_on_duty = request.user.is_available
            profile.save()
        except HealthWorkerProfile.DoesNotExist:
            pass
        
        return JsonResponse({
            'status': 'success',
            'is_available': request.user.is_available
        })
    
    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required
def user_list_view(request):
    """View for listing users (Admin only)."""
    if not request.user.is_admin_user:
        return redirect('accounts:dashboard_redirect')
    
    role_filter = request.GET.get('role', '')
    search_query = request.GET.get('q', '')
    
    users = User.objects.all()
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    users = users.order_by('-date_joined')
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'search_query': search_query,
        'total_count': users.count(),
    }
    return render(request, 'accounts/user_list.html', context)


@login_required
def user_detail_view(request, user_id):
    """View user details (Admin only)."""
    if not request.user.is_admin_user:
        return redirect('accounts:dashboard_redirect')
    
    user = get_object_or_404(User, id=user_id)
    
    # Get user appointments
    appointments = Appointment.objects.filter(
        Q(resident=user) | Q(health_worker=user)
    ).order_by('-scheduled_date')[:10]
    
    context = {
        'viewed_user': user,
        'appointments': appointments,
    }
    return render(request, 'accounts/user_detail.html', context)


@login_required
def user_activate_view(request, user_id):
    """Activate/Deactivate user account (Admin only)."""
    if not request.user.is_admin_user:
        return redirect('accounts:dashboard_redirect')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User account {status} successfully.')
    
    return redirect('accounts:user_list')
