from google.cloud import pubsub_v1
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser
import threading

PROJECT_ID = "directed-bongo-444307-p7"
SUBSCRIPTION_NAME = "exchange-notifications-sub"

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_NAME)

channel_layer = get_channel_layer()

def get_user_id_from_username(username):
    """Fetch user ID from the database using the username."""
    try:
        user = CustomUser.objects.get(username=username)
        return user.id
    except ObjectDoesNotExist:
        return None

def callback(message):
    """Processes Pub/Sub messages and sends WebSocket notifications."""
    data = json.loads(message.data.decode("utf-8"))
    print(f"📩 Received Pub/Sub message: {data}")  # Debugging

    receiver_id = get_user_id_from_username(data["receiver"])
    if receiver_id:
        async_to_sync(channel_layer.group_send)(
            f"user_{receiver_id}",
            {
                "type": "send_notification",
                "message": {
                    "event_type": data["event_type"],
                    "sender": data["sender"],
                    "receiver": data["receiver"],
                    "message": f"New notification: {data['event_type']} from {data['sender']}",
                },
            },
        )
    message.ack()

def handle():
    """Starts listening for Pub/Sub messages."""
    print("Pub sub subscriber started")
    future = subscriber.subscribe(subscription_path, callback=callback)
    try:
        future.result()
    except KeyboardInterrupt:
        future.cancel()

def start_pubsub_listener():
    """Starts the Pub/Sub listener in a separate thread."""
    thread = threading.Thread(target=handle, daemon=True)
    thread.start()
