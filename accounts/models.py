from django.contrib.auth.models import AbstractUser
from django.db import models
import random

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    phone_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    plain_text_password = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(max_length=10, default='en', choices=[
        ('en', 'English'),
        ('fr', 'French'),
        ('es', 'Spanish'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('pt', 'Portuguese'),
        ('ja', 'Japanese'),
        ('zh', 'Chinese'),
        ('ar', 'Arabic'),
        ('ru', 'Russian'),
        ('ko', 'Korean'),
        ('nl', 'Dutch'),
        ('tr', 'Turkish'),
        ('hi', 'Hindi'),
        ('sw', 'Swahili'),
    ])

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    
    def get_initials(self):
        """Get user initials for avatar"""
        first_initial = self.first_name[0].upper() if self.first_name else ''
        last_initial = self.last_name[0].upper() if self.last_name else ''
        return first_initial + last_initial
    
    def get_avatar_color(self):
        """Get a consistent color for user avatar based on email"""
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
            '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2'
        ]
        # Use email hash to get consistent color
        color_index = hash(self.email) % len(colors)
        return colors[color_index]

class Profile(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('personal', 'Personal Account'),
        ('business', 'Business Account'),
    ]
    
    COUNTRY_CHOICES = [
        ('US', '🇺🇸 United States'),
        ('CA', '🇨🇦 Canada'),
        ('GB', '🇬🇧 United Kingdom'),
        ('DE', '🇩🇪 Germany'),
        ('FR', '🇫🇷 France'),
        ('ES', '🇪🇸 Spain'),
        ('IT', '🇮🇹 Italy'),
        ('AU', '🇦🇺 Australia'),
        ('JP', '🇯🇵 Japan'),
        ('BR', '🇧🇷 Brazil'),
        ('MX', '🇲🇽 Mexico'),
        ('IN', '🇮🇳 India'),
        ('CN', '🇨🇳 China'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('de', 'Deutsch'),
        ('fr', 'Français'),
        ('es', 'Español'),
        ('it', 'Italiano'),
        ('ja', '日本語'),
        ('pt', 'Português'),
        ('zh', '中文'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='personal')
    country = models.CharField(max_length=5, choices=COUNTRY_CHOICES, default='US')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.get_account_type_display()}"

class ContactRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    CONTACT_TYPE_CHOICES = [
        ('phone', 'Phone Call'),
        ('email', 'Email Support'),
        ('chat', 'Live Chat'),
        ('form', 'Contact Form'),
    ]
    
    # Contact form fields
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES, default='form')
    
    # Admin assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_contacts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Admin response
    admin_response = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.subject}"
    
    class Meta:
        ordering = ['-created_at']

class ChatSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    
    # Chat participants
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_chats')
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_chats', null=True, blank=True)
    
    # Chat details
    subject = models.CharField(max_length=200, default='Live Chat')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Chat: {self.user.email} - {self.agent.email if self.agent else 'Unassigned'}"

class ChatMessage(models.Model):
    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.sender.email}: {self.message[:50] if self.message else '[Media]'}..."
    
    class Meta:
        ordering = ['timestamp']

class ChatImage(models.Model):
    chat_message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='chat_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for message {self.chat_message.id}"

class ChatAudio(models.Model):
    chat_message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='audio_files')
    audio = models.FileField(upload_to='chat_audio/')
    duration = models.FloatField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Audio for message {self.chat_message.id}"
