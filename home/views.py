from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.shortcuts import render,redirect,get_object_or_404
from .models import Skill,CustomUser,UserSkill,ExchangeRequest,PasswordResetOTP,SkillSahyogProfile,ChatAccess
from .models import ChatRoom,Message,SkillRequest,Notification,Feedback,ContactMessage
from django.contrib.auth import login,authenticate,logout,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import random,re,json,uuid
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect,csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q,Avg,Count,F,Value
from google.cloud import pubsub_v1
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from django.db.models.functions import Coalesce
from itertools import chain

User = get_user_model()

PROJECT_ID = "directed-bongo-444307-p7"
TOPIC_NAME = "exchange-notifications"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)

def publish_notification(event_type, sender, receiver):
    """ Publishes a message to Pub/Sub and stores it in the Notification model. """
    try:
        message = {
            "event_type": event_type,
            "sender": sender.username,
            "receiver": receiver.username
        }
        #Save notification to the database (for offline users to fetch later)
        Notification.objects.create(
             event_type=event_type,
             sender=sender,
             receiver=receiver,
             message=f"New notification: {event_type} from {sender.username}",
         )
        
        # Publish the notification to Pub/Sub for real-time delivery
        data = json.dumps(message).encode("utf-8")
        publisher.publish(topic_path, data=data)

    except Exception as e:
        print(f"Error publishing notification: {e}")  # Consider logging this error properly


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
        
        try:
            user = CustomUser.objects.get(username=username)
            if not user.is_active:
                messages.error(request, "Your account has been disabled. Please contact support for assistance.")
                return redirect('signin')
        except CustomUser.DoesNotExist:
                pass  # We'll handle the error message after authentication

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('dashboard')
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
    completed_requests = ExchangeRequest.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status='completed'
    )
    sent_requests = ExchangeRequest.objects.filter(sender=request.user)

    # Combine counts of sender_skill and receiver_skill
    sender_skill_counts = ExchangeRequest.objects.filter(status='completed') \
        .values(skill_name=F('sender_skill__skill_name')) \
        .annotate(total=Count('id'))

    receiver_skill_counts = ExchangeRequest.objects.filter(status='completed') \
        .values(skill_name=F('receiver_skill__skill_name')) \
        .annotate(total=Count('id'))

    # Merge the counts manually
    combined = {}
    for entry in chain(sender_skill_counts, receiver_skill_counts):
        skill_name = entry['skill_name']
        combined[skill_name] = combined.get(skill_name, 0) + entry['total']

    # Sort by total exchanges and take top 5
    sorted_skills = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:2]
    suggested_skills = [skill for skill, count in sorted_skills]

    # Other data
    notifications = Notification.objects.filter(receiver=request.user).order_by('-timestamp')[:1]
    skillsahyog_rank_details = SkillSahyogProfile.objects.get(user=request.user)
    user_skills = UserSkill.objects.filter(user=request.user)
    selected_skill = random.choice(user_skills) if user_skills.exists() else None

    active_chats = ChatAccess.objects.filter(
        (Q(user1=request.user) | Q(user2=request.user)), is_active=True
    ).select_related('exchange')

    chat_rooms = [
        {
            "user1": chat.user1,
            "user2": chat.user2,
            "room_id": chat.exchange.chatroom.room_id
        }
        for chat in active_chats if hasattr(chat.exchange, 'chatroom')
    ]

    context = {
        'rank_details': skillsahyog_rank_details,
        'selected_skill': selected_skill,
        'pending_requests': pending_requests,
        'pending_requests_count': pending_requests.count(),
        'completed_requests_count': completed_requests.count(),
        'active_chats': chat_rooms,
        'notifications': notifications,
        'sent_requests_count': sent_requests.count(),
        'suggested_skills': suggested_skills,
    }

    # Add unread contact messages if superuser
    if request.user.is_superuser:
        context['unread_contact_messages'] = ContactMessage.objects.filter(is_read=False).order_by('-submitted_at')

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
    completed_requests = ExchangeRequest.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status='completed'
    )

    return render(request, 'profile.html', {
        'profile_user': profile_user,
        'user_skills': user_skills,
        'completed_requests_count':completed_requests.count(),
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
            defaults={"room_id": uuid.uuid4().hex[:12]}  
        )

        ChatAccess.objects.get_or_create(
            user1=exchange_request.sender,
            user2=exchange_request.receiver,
            exchange=exchange_request,
            is_active=True
        )

        publish_notification("exchange_accepted", request.user, exchange_request.sender)

        return redirect("chat_page", chat_id=chatroom.room_id)

    return JsonResponse({"message": "Invalid request or already processed."}, status=400)


@login_required
def reject_exchange_request(request, request_id):
    exchange_request = get_object_or_404(ExchangeRequest, id=request_id, receiver=request.user)

    if exchange_request.status == 'pending':
        exchange_request.status = 'rejected'
        exchange_request.save()
        
        publish_notification("exchange_rejected", request.user, exchange_request.sender)

        # Redirect to dashboard after rejection
        return redirect('dashboard')

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
            publish_notification("exchange_request", request.user, receiver)
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

    # Get the exchange object
    exchange = chat_room.exchange

    # Determine the other user involved in the exchange
    other_user = exchange.sender if exchange.receiver == request.user else exchange.receiver

    # Check if the other user has submitted feedback
    other_user_feedback = Feedback.objects.filter(exchange=exchange, giver=other_user).exists()
    current_user_feedback = Feedback.objects.filter(exchange=exchange, giver=request.user).exists()


    return render(request, "message.html", {
        "active_chat": chat_room,
        "chat_id": chat_room.room_id,
        "chat_access": chat_access,
        "messages":messages,
        "exchange_id":chat_room.exchange_id,
        "other_user_feedback": other_user_feedback,
        "current_user_feedback": current_user_feedback,
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
def feedback(request, exchange_id):
    # Get the exchange request or 404 if not found
    print("[DEBUG] Feedback view triggered.")
    exchange = get_object_or_404(ExchangeRequest, id=exchange_id)

   # Check if the user is allowed to give feedback (i.e., coming from chatroom or feedback page)
    referer = request.META.get('HTTP_REFERER')
    if not referer or (f"/chat/{exchange.chatroom.room_id}/" not in referer and f"/feedback/{exchange_id}/" not in referer):
        print("[DEBUG] Not allowed directly")
        messages.error(request, "You are not allowed to access the feedback page directly.")
        return redirect('dashboard')

    # Check if feedback already exists for this exchange and user
    if Feedback.objects.filter(exchange=exchange, giver=request.user).exists():
        print("[DEBUG]already submitted")
        messages.info(request, "You have already submitted feedback for this exchange.")
        return redirect('dashboard')

    # Handle form submission
    if request.method == "POST":
        feedback_text = request.POST.get("feedback")
        skill_score = float(request.POST.get("skill_score"))
        rating = int(request.POST.get("rating"))

        feedback = Feedback.objects.create(
            exchange=exchange,
            giver=request.user,
            receiver=exchange.receiver if exchange.sender == request.user else exchange.sender,
            feedback_text=feedback_text,
            rating=rating,
            skill_score=skill_score,
            is_completed=True
        )

        # Check if both users have submitted feedback
        if Feedback.objects.filter(exchange=exchange).count() == 2:
            # Deactivate the chat
            chat_access = ChatAccess.objects.get(exchange=exchange)
            chat_access.is_active = False
            chat_access.save()

            # Update the status of the exchange to 'completed'
            exchange.status = 'completed'
            exchange.save()
            print("[DEBUG] Exchange status updated to completed.")


            # Update both users' SkillSahyogProfile scores
            feedbacks = Feedback.objects.filter(exchange=exchange)
            for fb in feedbacks:
                try:
                    # Credit the score to the **receiver** of the feedback
                    profile = SkillSahyogProfile.objects.get(user=fb.receiver)
                    profile.score += int(fb.skill_score)
                    profile.update_rank()  # Update the rank based on the new score
                    profile.save()
                    print(f"[DEBUG] Updated profile for {fb.receiver.username} with score {fb.skill_score}")
                except SkillSahyogProfile.DoesNotExist:
                    print(f"[ERROR] No profile found for user {fb.receiver.username}")

        messages.success(request, "Feedback submitted successfully.")
        return redirect('dashboard')
    status = "Completed"

    context = {
        'exchange': exchange,
        'status': status,
        'skill_score': 0.0  # Default value before submission
    }
    return render(request, 'feedback.html', context)

@login_required
def profile_settings(request):
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

def notification(request):
    notifications = Notification.objects.filter(receiver=request.user).order_by('-timestamp')
    context = {
        'notifications':notifications,
    }
    return render(request,"notifications.html",context)

@login_required
def calculate_skill_score(request, exchange_id):
    if request.method == "POST":
        try:
            rating = int(request.POST.get("rating"))
            exchange = get_object_or_404(ExchangeRequest, id=exchange_id)

            # Create a temporary feedback object without saving
            feedback = Feedback(exchange=exchange, rating=rating, giver=request.user, receiver=exchange.receiver)
            feedback.skill_score = feedback.calculate_skill_score()

            return JsonResponse({"skill_score": feedback.skill_score}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def view_feedbacks(request):
    # Feedbacks given by the current user
    given_feedbacks = Feedback.objects.filter(giver=request.user).select_related('exchange', 'receiver').order_by('-timestamp')
    
    # Feedbacks received by the current user
    received_feedbacks = Feedback.objects.filter(receiver=request.user).select_related('exchange', 'giver').order_by('-timestamp')

    context = {
        'given_feedbacks': given_feedbacks,
        'received_feedbacks': received_feedbacks,
    }
    return render(request, 'my_ratings.html', context)

@login_required
def view_exchanges(request):
    exchanges = ExchangeRequest.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('sender', 'receiver')

    # Attach ChatRoom and ChatAccess to each exchange
    for exchange in exchanges:
        exchange.attached_chatroom = ChatRoom.objects.filter(exchange=exchange).first()
        exchange.chat_access = ChatAccess.objects.filter(exchange=exchange).first()

    return render(request, 'my_exchanges.html', {'exchanges': exchanges})

@login_required
def account_settings(request):
    user = request.user
    success_message = None  # Initialize success message

    if request.method == 'POST':
        # Update editable fields
        first_name = request.POST.get('first_name', user.first_name)
        last_name = request.POST.get('last_name', user.last_name)
        bio = request.POST.get('bio', user.bio)
        location = request.POST.get('location', user.location)
        profile_picture = request.FILES.get('profile_picture', user.profile_picture)

        # Update user object with new values
        user.first_name = first_name
        user.last_name = last_name
        user.bio = bio
        user.location = location
        if profile_picture:
            user.profile_picture = profile_picture

        # Save the updated user object
        user.save()
        success_message = "Your account settings have been updated successfully!"  # Set success message

    context = {
        'user': user,
        'success_message': success_message,  # Pass success message to the template
    }
    return render(request, 'accounts.html', context) 

def disable_account(request):
    if request.method == 'POST':
        user = request.user
        user.is_active = False
        user.save()
        logout(request)
        messages.success(request, "Your account has been disabled successfully.")
        return redirect('homepage')
    return redirect('settings')  # Fallback in case of a GET request

@login_required
def match_skill(request):
    skills = Skill.objects.all()
    selected_skill_id = request.GET.get("skill_id")
    matched_users_with_scores = []

    if selected_skill_id:
        # Step 1: Filter users with the selected skill
        user_skills = UserSkill.objects.filter(skill_id=selected_skill_id)
        user_ids = user_skills.values_list("user_id", flat=True).distinct()

        raw_data = []

        # Step 2: Collect score and avg_rating for users
        for user_id in user_ids:
            try:
                profile = SkillSahyogProfile.objects.get(user_id=user_id)
                score = profile.score

                feedbacks = Feedback.objects.filter(receiver_id=user_id)
                avg_rating = feedbacks.aggregate(avg=Avg("rating"))["avg"] or 0

                raw_data.append((user_id, profile.user, score, avg_rating))
            except SkillSahyogProfile.DoesNotExist:
                continue

        if raw_data:
            # Step 3: Normalize score and avg_rating
            scores = np.array([d[2] for d in raw_data]).reshape(-1, 1)
            ratings = np.array([d[3] for d in raw_data]).reshape(-1, 1)

            # Initialize MinMaxScaler
            scaler_score = MinMaxScaler()
            scaler_rating = MinMaxScaler()

            # Scale the scores and ratings
            norm_scores = scaler_score.fit_transform(scores).flatten()
            norm_ratings = scaler_rating.fit_transform(ratings).flatten()

            # Step 4: Use trained weights and bias
            weight_score = 0.60
            weight_rating = 10.43
            bias = -2.17

            for i, (user_id, user_obj, raw_score, raw_rating) in enumerate(raw_data):
                # Calculate the match quality score (AI score) using the formula
                ai_score = (weight_score * norm_scores[i]) + (weight_rating * norm_ratings[i]) + bias

                matched_users_with_scores.append({
                    "user": user_obj,
                    "score": raw_score,
                    "avg_rating": round(raw_rating, 2),
                    "ai_score": ai_score
                })

            # Sort matched users by the AI score in descending order
            matched_users_with_scores.sort(key=lambda x: x["ai_score"], reverse=True)

    context = {
        "skills": skills,
        "selected_skill_id": int(selected_skill_id) if selected_skill_id else None,
        "matched_users": matched_users_with_scores,
    }

    return render(request, "match_skills.html", context)

def privacy_policy(request):
    return render(request,"privacy_policy.html")

def terms_and_conditions(request):
    return render(request,"terms.html")

@csrf_exempt  # Optional: only if you're not including {% csrf_token %} in your form
def submit_contact_form(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        message = request.POST.get('message')

        if username and email and message:
            ContactMessage.objects.create(username=username, email=email, message=message)
        
        return redirect('homepage')  # Make sure this name matches your url for index.html

    return redirect('features')  # fallback

@require_POST
@login_required
def mark_contact_message_read(request, message_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        msg = ContactMessage.objects.get(id=message_id, is_read=False)
        msg.is_read = True
        msg.save()
        return JsonResponse({'success': True})
    except ContactMessage.DoesNotExist:
        return JsonResponse({'error': 'Message not found or already read'}, status=404)
    
@staff_member_required
def manage_users(request):
    query = request.GET.get('q')
    users = User.objects.all().order_by('-date_joined')

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'manage_users.html', {'page_obj': page_obj})

@staff_member_required
def toggle_user_status(request, user_id):
    user = User.objects.get(id=user_id)
    user.is_active = not user.is_active
    user.save()
    return redirect('manage_users')

def about(request):
    return render(request,'about.html')
