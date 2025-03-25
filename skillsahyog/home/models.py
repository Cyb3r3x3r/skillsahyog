from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import uuid

class Skill(models.Model):
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
        if self.score >= 101:
            self.rank = "Master Connector"
        elif self.score >= 61:
            self.rank = "Expert Guide"
        elif self.score >= 31:
            self.rank = "Skilled Mentor"
        elif self.score >= 11:
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