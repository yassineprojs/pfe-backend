# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, PendingUser, Analyst, Admin
import uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.urls import reverse





def request_access(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        role = request.POST.get('role')
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return redirect('users:request_access')
        if PendingUser.objects.filter(email=email).exists():
            messages.warning(request, "An access request is already pending for this email.")
            return redirect('users:request_access')
        PendingUser.objects.create(email=email, role=role)
        messages.success(request, "Your access request has been submitted. Await admin approval.")
        return redirect('users:login')
    return render(request, 'users/request_access.html')

def register(request, token):
    pending_user = get_object_or_404(PendingUser, token=token)
    user = CustomUser.objects.get(email=pending_user.email)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('users:register', token=token)
        user.username = username
        user.set_password(password)
        user.save()
        if pending_user.role == 'Analyst':
            Analyst.objects.get_or_create(user=user)
        else:
            Admin.objects.get_or_create(user=user)
        pending_user.delete()
        messages.success(request, "Account created successfully. Please log in.")
        return redirect('users:login')
    return render(request, 'users/register.html', {'email': pending_user.email})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.is_approved:
            login(request, user)
            if hasattr(user, 'analyst'):
                return redirect('incidents:dashboard')  # Adjust to your app's dashboard URL
            elif hasattr(user, 'admin'):
                return redirect('admin:index')
        messages.error(request, "Invalid credentials or account not approved.")
    return render(request, 'users/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('users:login')

@user_passes_test(lambda u: u.is_superuser)
def approve_user(request, pk):
    pending_user = get_object_or_404(PendingUser, pk=pk)
    user = CustomUser.objects.create(
        username=pending_user.email.split('@')[0],  # Temporary username
        email=pending_user.email,
        is_approved=True
    )
    if pending_user.role == 'Analyst':
        Analyst.objects.create(user=user)
    else:
        Admin.objects.create(user=user)
    token = str(pending_user.token)
    register_url = request.build_absolute_uri(reverse('users:register', args=[token]))
    send_mail(
        "SOC Access Approved",
        f"Complete your registration here: {register_url}",
        settings.EMAIL_HOST_USER,
        [pending_user.email],
        fail_silently=False,
    )
    pending_user.delete()
    messages.success(request, f"User {pending_user.email} approved and notified.")
    return redirect('admin:users_pendinguser_changelist')

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user and user.is_approved:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'message': 'Login successful',
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'isAnalyst': hasattr(user, 'analyst'),
                'isAdmin': hasattr(user, 'admin')
            }
        }, status=200)
    return Response({'error': 'Invalid credentials or account not approved'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    request.user.auth_token.delete()  # Delete token
    logout(request)
    return Response({'message': 'Logged out successfully'}, status=200)