from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import uuid

class Skill(models.Model):
    id = models.AutoField(primary_key=True)
    skill_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.skill_name
    

class CustomUser(AbstractUser):
    dob = models.DateField(null=True, blank=True)
    sex_choices = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('transgender', 'Transgender'),
        ('other', 'Other')
    ]
    sex = models.CharField(max_length=20, choices=sex_choices, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    profile_verified = models.BooleanField(default=False)


    # Many-to-Many Relationship with Skills
    skills = models.ManyToManyField(Skill, blank=True)

    def __str__(self):
        return self.username
    
class Notification(models.Model):
    EXCHANGE_REQUEST = "exchange_request"
    OTHER = "other"

    EVENT_TYPES = [
        (EXCHANGE_REQUEST, "Exchange Request"),
        (OTHER, "Other"),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    sender = models.ForeignKey(CustomUser, related_name="sent_notifications", on_delete=models.SET_NULL,null=True)
    receiver = models.ForeignKey(CustomUser, related_name="received_notifications", on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)  # Track unread notifications
    timestamp = models.DateTimeField(auto_now_add=True)

    def mark_as_read(self):
        self.is_read = True
        self.save()

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.event_type} ({'Read' if self.is_read else 'Unread'})"

class PasswordResetOTP(models.Model):
    user= models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    otp=models.CharField(max_length=6)
    def __str__(self):
        return f"{self.user.username} - OTP: {self.otp}"
    
class UserSkill(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    skill_levels = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert')
    ]
    skill_level = models.CharField(max_length=15, choices=skill_levels)

    class Meta:
        unique_together = ('user', 'skill')

    def __str__(self):
        return f"{self.user.username} - {self.skill.skill_name} ({self.skill_level})"
    
class ExchangeRequest(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_requests')
    sender_skill = models.ForeignKey(Skill, related_name='sent_skill_exchanges', on_delete=models.CASCADE,default=1)
    receiver_skill = models.ForeignKey(Skill, related_name='received_skill_exchanges', on_delete=models.CASCADE,default=1)
    status_choices = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed','Completed'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver', 'sender_skill', 'receiver_skill')  # Ensures unique skill exchange requests


    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username} ({self.status})"

class SkillSahyogProfile(models.Model):
    RANK_CHOICES = [
        ("Beginner", "Beginner"),
        ("Apprentice", "Apprentice"),
        ("Skilled Mentor", "Skilled Mentor"),
        ("Expert Guide", "Expert Guide"),
        ("Master Connector", "Master Connector"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="skill_profile")
    score = models.IntegerField(default=0)
    rank = models.CharField(max_length=20, choices=RANK_CHOICES, default="Beginner")

    def update_rank(self):
        """ Update rank based on score """
        if self.score >= 1500:
            self.rank = "Master Connector"
        elif self.score >= 610:
            self.rank = "Expert Guide"
        elif self.score >= 310:
            self.rank = "Skilled Mentor"
        elif self.score >= 150:
            self.rank = "Apprentice"
        else:
            self.rank = "Beginner"
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.rank} ({self.score} points)"

class ChatAccess(models.Model):
    user1 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="chat_user1")
    user2 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="chat_user2")
    exchange = models.OneToOneField(ExchangeRequest, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)  # Chat is open while exchange is active

    def close_chat(self):
        """Close chat when exchange is completed or revoked."""
        self.is_active = False
        self.save()
    
class ChatRoom(models.Model):
    exchange = models.OneToOneField(ExchangeRequest, on_delete=models.CASCADE)
    room_id = models.CharField(max_length=20, unique=True, default=uuid.uuid4().hex[:12])

    def __str__(self):
        return f"Chat Room {self.room_id} for {self.exchange}"

class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} at {self.timestamp}"
    

class SkillRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    skill_name = models.CharField(max_length=100, unique=True)
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} requested {self.skill_name}"
    
class Feedback(models.Model):
    exchange = models.ForeignKey(ExchangeRequest, on_delete=models.CASCADE, related_name='feedback')
    giver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='given_feedbacks')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_feedbacks')
    feedback_text = models.TextField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(default=0)  # Rating out of 5
    skill_score = models.FloatField(default=0.0)  # Calculated skill score
    timestamp = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)  # Whether feedback has been submitted

    def __str__(self):
        return f"Feedback from {self.giver.username} to {self.receiver.username} (Exchange ID: {self.exchange.id})"

    def calculate_skill_score(self):
        # Skill the user received help with (exchange partner's skill)
        skill = self.exchange.receiver_skill  

        # Count how many times this skill has been involved in exchanges (either as sender or receiver)
        total_requests = ExchangeRequest.objects.filter(
            models.Q(receiver_skill=skill) | models.Q(sender_skill=skill)
        ).count()

        # Get the maximum number of requests for any skill
        max_requests = ExchangeRequest.objects.values('receiver_skill').annotate(
            request_count=models.Count('receiver_skill') + models.Count('sender_skill')
        ).order_by('-request_count').first()
        max_requests_count = max_requests['request_count'] if max_requests else 1  # Avoid division by zero

        # Normalize the demand score between 0 and 1
        normalized_demand = total_requests / max_requests_count  

        # Rating Normalization (scaled between 0 and 1)
        normalized_rating = self.rating / 5  

        # Skill Score Calculation (Weighted Average)
        alpha = 0.6  # Weight for skill demand
        beta = 0.4   # Weight for rating
        self.skill_score = 100 * ((alpha * normalized_demand) + (beta * normalized_rating))
        return self.skill_score