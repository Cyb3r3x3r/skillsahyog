from django.shortcuts import render,redirect,get_object_or_404
from .models import Skill,CustomUser,UserSkill,ExchangeRequest,PasswordResetOTP,SkillSahyogProfile,ChatAccess
from .models import ChatRoom,Message,SkillRequest
from django.contrib.auth import login,authenticate,logout,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import random,re,json,uuid
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q

# Create your views here.
def homepage(request):
    return render(request,'index.html')

def features(request):
    return render(request,'features.html')

def howitworks(request):
    return render(request,'howitworks.html')

def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    skills = Skill.objects.all()  # Fetch skills from the database

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        dob = request.POST.get("dob")
        sex = request.POST.get("sex")
        phone_number = request.POST.get("phone_number")
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")
        bio = request.POST.get("bio")
        location = request.POST.get("location")
        profile_picture = request.FILES.get("profile_picture")

        # Create the user
        user = CustomUser.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name, dob=dob,
            sex=sex, phone_number=phone_number, bio=bio,
            location=location, profile_picture=profile_picture
        )

        # Create the Skill Sahyog Profile
        SkillSahyogProfile.objects.create(user=user)

        # Add selected skills to the user
        selected_skills = request.POST.getlist("skills")
        for skill_id in selected_skills:
            skill = Skill.objects.get(id=skill_id)
            skill_level = request.POST.get(f"skill_level_{skill_id}")
            UserSkill.objects.create(user=user, skill=skill, skill_level=skill_level)

        # Automatically log the user in after signup
        login(request, user)
        
        return redirect('dashboard')

    return render(request, 'signup.html', {'skills': skills})

def signin(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('dashboard')  # Redirect to dashboard after login
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    
    return render(request, 'signin.html')

def check_username_availability(request):
    username = request.GET.get("username", None)
    if username and CustomUser.objects.filter(username=username).exists():
        return JsonResponse({"available": False}, status=200)
    return JsonResponse({"available": True}, status=200)

@login_required
def dashboard(request):
    pending_requests = ExchangeRequest.objects.filter(receiver=request.user, status='pending')
    pending_requests_count = pending_requests.count()  # Count pending requests
    completed_requests = ExchangeRequest.objects.filter(receiver=request.user, status='completed')
    completed_requests_count = completed_requests.count()  # Count completed requests
    
    skillsahyog_rank_details = SkillSahyogProfile.objects.get(user=request.user)
    user_skills = UserSkill.objects.filter(user=request.user)  # Get user's skills with levels
    selected_skill = random.choice(user_skills) if user_skills.exists() else None
    active_chats = ChatAccess.objects.filter(
        (Q(user1=request.user) | Q(user2=request.user)), is_active=True
    ).select_related('exchange')
    chat_rooms = [
        {
            "user1": chat.user1,
            "user2": chat.user2,
            "room_id": chat.exchange.chatroom.room_id  # Fetch the associated ChatRoom ID
        }
        for chat in active_chats if hasattr(chat.exchange, 'chatroom')
    ]

    context = {
        'rank_details':skillsahyog_rank_details,
        'selected_skill': selected_skill,
        'pending_requests': pending_requests,
        'pending_requests_count': pending_requests_count,
        'completed_requests_count': completed_requests_count,
        'active_chats':chat_rooms,
    }
    return render(request, 'dashboard.html', context)

def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('signin')

# def message(request):
#     return render(request,'message.html')

def user_profile(request, username):
    profile_user = get_object_or_404(CustomUser, username=username)
    user_skills = UserSkill.objects.filter(user=profile_user)  # Fetch skills with levels
    skillsahyog_rank_details = SkillSahyogProfile.objects.get(user=request.user)

    return render(request, 'profile.html', {
        'profile_user': profile_user,
        'user_skills': user_skills,
        'rank_details':skillsahyog_rank_details,
    })


@login_required
def accept_exchange_request(request, request_id):
    exchange_request = get_object_or_404(ExchangeRequest, id=request_id, receiver=request.user)

    if exchange_request.status == 'pending':
        exchange_request.status = 'accepted'
        exchange_request.save()

        chatroom, created = ChatRoom.objects.get_or_create(
        exchange=exchange_request,
        defaults={"room_id": uuid.uuid4().hex[:12]}  # Ensure unique room_id
    )

        # Ensure chat access exists
        ChatAccess.objects.get_or_create(
            user1=exchange_request.sender,
            user2=exchange_request.receiver,
            exchange=exchange_request,
            is_active=True
        )

        
        # Redirect to chat room page
        return redirect("chat_page", chat_id=chatroom.room_id)

    return JsonResponse({"message": "Invalid request or already processed."}, status=400)


@login_required
def reject_exchange_request(request, request_id):
    exchange_request = get_object_or_404(ExchangeRequest, id=request_id, receiver=request.user)

    if exchange_request.status == 'pending':
        exchange_request.status = 'rejected'
        exchange_request.save()
        return JsonResponse({"message": "Exchange request rejected."})

    return JsonResponse({"message": "Invalid request."}, status=400)

@login_required
def send_exchange_request(request, receiver_id):
    receiver = get_object_or_404(CustomUser, id=receiver_id)

    if request.user == receiver:
        messages.error(request, "You cannot send a request to yourself.")
        return redirect('user_profile', username=receiver.username)

    user_skills = UserSkill.objects.filter(user=request.user)
    receiver_skills = UserSkill.objects.filter(user=receiver)

    common_skills = user_skills.filter(skill__in=receiver_skills.values('skill'))

    if request.method == "POST":
        sender_skill_id = request.POST.get("sender_skill")
        receiver_skill_id = request.POST.get("receiver_skill")

        if not sender_skill_id or not receiver_skill_id:
            messages.error(request, "Please select skills for the exchange.")
            return redirect('user_profile', username=receiver.username)

        sender_skill = get_object_or_404(Skill, id=sender_skill_id)
        receiver_skill = get_object_or_404(Skill, id=receiver_skill_id)

        # Check if an exchange request with the same skills already exists
        existing_request = ExchangeRequest.objects.filter(
            sender=request.user, 
            receiver=receiver, 
            sender_skill=sender_skill, 
            receiver_skill=receiver_skill
        ).exists()

        if existing_request:
            messages.error(request, "You have already sent a request with these skills.")
        else:
            ExchangeRequest.objects.create(
                sender=request.user, 
                receiver=receiver, 
                sender_skill=sender_skill, 
                receiver_skill=receiver_skill
            )
            messages.success(request, "Exchange request sent successfully.")

        return redirect('user_profile', username=receiver.username)

    return render(request, 'send_exchange_request.html', {
        'receiver': receiver,
        'common_skills': common_skills
    })

def forgot_password_request(request):
    if request.method == "POST":
        username = request.POST.get("username")

        try:
            user = CustomUser.objects.get(username=username)
            otp = random.randint(100000, 999999)

            # Store OTP in the database
            PasswordResetOTP.objects.update_or_create(user=user, defaults={"otp": otp})

            # Send OTP via Email
            send_mail(
                "Password Reset OTP",
                f"Your OTP for password reset is: {otp}",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            # Store username in session
            request.session["reset_username"] = username
            messages.success(request, "OTP sent successfully! Please check your email.")
            return redirect("forgot_password_verify")

        except CustomUser.DoesNotExist:
            messages.error(request, "User not found!")
            return redirect("forgot_password_request")

    return render(request, "forgot_password_request.html")


def forgot_password_verify(request):
    if "reset_username" not in request.session:
        return redirect("forgot_password_request")  # Ensure user follows the correct flow

    if request.method == "POST":
        username = request.session.get("reset_username")
        otp_entered = request.POST.get("otp")

        try:
            user = CustomUser.objects.get(username=username)
            otp_record = PasswordResetOTP.objects.get(user=user)

            if str(otp_record.otp) == otp_entered:
                messages.success(request, "OTP verified! Now set your new password.")
                return redirect("forgot_password_reset")

            else:
                messages.error(request, "Invalid OTP! Try again.")
                return redirect("forgot_password_verify")

        except (CustomUser.DoesNotExist, PasswordResetOTP.DoesNotExist):
            messages.error(request, "OTP verification failed!")
            return redirect("forgot_password_request")

    return render(request, "forgot_password_verify.html")


def forgot_password_reset(request):
    if "reset_username" not in request.session:
        return redirect("forgot_password_request")  # Ensure user follows the correct flow

    if request.method == "POST":
        username = request.session.get("reset_username")
        new_password = request.POST.get("new_password")

        # Validate Password Strength
        password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not re.match(password_regex, new_password):
            messages.error(
                request,
                "Password must be at least 8 characters long and contain at least 1 uppercase, 1 lowercase, 1 number, and 1 special character."
            )
            return redirect("forgot_password_reset")

        try:
            user = CustomUser.objects.get(username=username)
            user.set_password(new_password)
            user.save()

            # Clear session
            del request.session["reset_username"]

            messages.success(request, "Password reset successful! You can now log in.")
            return redirect("signin")

        except CustomUser.DoesNotExist:
            messages.error(request, "User not found!")
            return redirect("forgot_password_request")

    return render(request, "forgot_password_reset.html")

@login_required
def chat_page(request, chat_id):
    """Render chat page if users have an active exchange request."""

    # Directly get active chat
    chat_access = ChatAccess.objects.filter(
        Q(user1=request.user) | Q(user2=request.user),
        is_active=True,
        exchange__chatroom__room_id=chat_id
    ).first()

    if not chat_access:
        return redirect("dashboard")  # Redirect if no active chat

    chat_room = get_object_or_404(ChatRoom, room_id=chat_id)

    messages = Message.objects.filter(chat_room=chat_room).order_by("timestamp")

    return render(request, "message.html", {
        "active_chat": chat_room,
        "chat_id": chat_room.room_id,
        "chat_access": chat_access,
        "messages":messages,
    })

from .serializers import ChatRoomSerializer,ChatAccessSerializer,MessageSerializer
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_chat_rooms(request):
    """Get all active chat rooms for the logged-in user."""
    chat_rooms = ChatRoom.objects.filter(exchange__chataccess__is_active=True).filter(
        exchange__chataccess__user1=request.user
    ) | ChatRoom.objects.filter(exchange__chataccess__user2=request.user)
    
    serializer = ChatRoomSerializer(chat_rooms, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_messages(request, chat_id):
    """Fetch messages for a chat room (only for authorized users)."""
    chat_room = get_object_or_404(ChatRoom, room_id=chat_id)

    chat_access = ChatAccess.objects.filter(
        Q(user1=request.user) | Q(user2=request.user),
        exchange__chatroom=chat_room,
        is_active=True
    ).first()

    if not chat_access:
        return Response({"error": "Unauthorized access"}, status=status.HTTP_403_FORBIDDEN)

    last_message_id = request.GET.get("last_message_id", 0)
    messages = Message.objects.filter(chat_room=chat_room, id__gt=last_message_id).order_by("timestamp").distinct()
    serializer = MessageSerializer(messages, many=True)

    return Response({"messages": serializer.data}, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message(request):
    """Send a message only if the user is part of the chat."""
    chat_id = request.data.get("chat_id")
    content = request.data.get("message")

    if not chat_id or not content:
        return Response({"error": "Chat ID and message are required."}, status=status.HTTP_400_BAD_REQUEST)

    chat_room = get_object_or_404(ChatRoom, room_id=chat_id)

    chat_access = ChatAccess.objects.filter(
        Q(user1=request.user) | Q(user2=request.user),
        exchange__chatroom=chat_room,
        is_active=True
    ).first()

    if not chat_access:
        return Response({"error": "Unauthorized to send messages in this chat."}, status=status.HTTP_403_FORBIDDEN)

    message = Message.objects.create(chat_room=chat_room, sender=request.user, content=content)
    serializer = MessageSerializer(message)

    return Response({"status": "Message sent", "message": serializer.data}, status=status.HTTP_201_CREATED)

@login_required
def manage_skills(request):
    user = request.user
    user_skills = UserSkill.objects.filter(user=user)  
    available_skills = Skill.objects.exclude(id__in=user_skills.values_list('skill_id', flat=True))  

    if request.method == "POST":
        if "add_skill" in request.POST:  
            skill_id = request.POST.get("skill")
            skill_level = request.POST.get("skill_level")

            if skill_id and skill_level:
                skill = Skill.objects.get(id=skill_id)
                UserSkill.objects.create(user=user, skill=skill, skill_level=skill_level)
                return redirect("manage_skills")

        elif "request_skill" in request.POST and not user.is_superuser:
            new_skill_name = request.POST.get("new_skill").strip()
            if new_skill_name and not Skill.objects.filter(skill_name__iexact=new_skill_name).exists():
                SkillRequest.objects.create(user=user, skill_name=new_skill_name)  # Save request
                return redirect("manage_skills")

        elif "approve_skill" in request.POST and user.is_superuser:
            skill_request_id = request.POST.get("skill_request_id")
            skill_request = SkillRequest.objects.get(id=skill_request_id)
            Skill.objects.create(skill_name=skill_request.skill_name)  # Add skill to DB
            skill_request.delete()  # Remove request after approval
            return redirect("manage_skills")

    skill_requests = SkillRequest.objects.all() if user.is_superuser else None  # Fetch requests only for superusers

    return render(request, "manage_skills.html", {
        "user_skills": user_skills,
        "available_skills": available_skills,
        "is_superuser": user.is_superuser,
        "skill_requests": skill_requests,
    })

@login_required
def feedback(request):
    return render(request,"feedback.html")

@login_required
def account_settings(request):
    user = request.user
    otp_sent = False

    if request.method == "POST":
        if "send_otp" in request.POST:
            otp = random.randint(100000, 999999)
            PasswordResetOTP.objects.update_or_create(user=user, defaults={"otp": otp})

            send_mail(
                "SkillSahyog Profile Verification OTP",
                f"Hello {user.username}! Your OTP for profile verification is: {otp}",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

            messages.success(request, "OTP sent successfully! Check your email.")
            otp_sent = True

        elif "verify_otp" in request.POST:
            entered_otp = request.POST.get("otp")

            try:
                otp_record = PasswordResetOTP.objects.get(user=user)

                if str(otp_record.otp) == entered_otp:
                    user.profile_verified = True
                    user.save()
                    otp_record.delete()

                    messages.success(request, "Profile verified successfully! ✅")
                else:
                    messages.error(request, "Invalid OTP! Please try again.")
            
            except PasswordResetOTP.DoesNotExist:
                messages.error(request, "No OTP found! Please request a new one.")

    return render(request, "settings.html", {"otp_sent": otp_sent})