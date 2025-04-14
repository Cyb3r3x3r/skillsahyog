import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Notification  # Assuming you have a Notification model

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

            print("[DEBUG] WebSocket Connection Accepted")

            # Fetch unread notifications asynchronously and send them
            await self.send_unread_notifications()
        else:
            print("[DEBUG] WebSocket Connection Denied (User Not Authenticated)")
            await self.close()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            print(f"[DEBUG] WebSocket Disconnecting: {self.user.username}")
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        print(f"[DEBUG] WebSocket Received Data: {text_data}")
        data = json.loads(text_data)
        # Handle incoming messages if needed

    async def send_notification(self, event):
        """ Send real-time notifications """
        notification_data = event["message"]

        # Mark notification as read when sent (optional)
        notification_id = notification_data.get("id")
        if notification_id:
            await self.mark_notification_as_read(notification_id)

        await self.send(text_data=json.dumps(notification_data))

    async def send_unread_notifications(self):
        """ Fetch and send stored notifications when the user connects """
        unread_notifications = await self.get_unread_notifications()

        print(f"[DEBUG] Unread Notifications Found: {len(unread_notifications)}")

        for notification in unread_notifications:
            notification_data = {
                "id": notification.id,
                "event_type": notification.event_type,
                "message": notification.message,
                "timestamp": str(notification.timestamp),
                "is_read": notification.is_read,
            }
            print(f"[DEBUG] Sending Stored Notification: {notification_data}")
            await self.send(text_data=json.dumps(notification_data))

            # Mark notification as read when sent
            await self.mark_notification_as_read(notification.id)

    @sync_to_async
    def get_unread_notifications(self):
        """ Fetch unread notifications for the user asynchronously """
        try:
            unread_notifications = Notification.objects.filter(receiver=self.user, is_read=False).order_by("timestamp")
            return list(unread_notifications)  # Convert to list to avoid lazy evaluation in async context
        except Exception as e:
            print(f"[ERROR] Failed to Fetch Unread Notifications: {e}")
            return []

    @sync_to_async
    def mark_notification_as_read(self, notification_id):
        """ Mark a notification as read asynchronously """
        try:
            updated_count = Notification.objects.filter(id=notification_id).update(is_read=True)
            print(f"[DEBUG] Marked Notification {notification_id} as Read (Updated: {updated_count})")
        except Exception as e:
            print(f"[ERROR] Failed to Mark Notification as Read: {e}")
