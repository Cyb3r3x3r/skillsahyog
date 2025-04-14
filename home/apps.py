from django.apps import AppConfig
import os
import threading

class HomeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "home"

    pubsub_started = False

    def ready(self):
        """Start Pub/Sub listener only in the main process."""
        from home.pub_sub import start_pubsub_listener

        # Ensure it runs only once and not in migrations
        if not HomeConfig.pubsub_started and os.environ.get("RUN_MAIN") == "true":
            print("🚀 Starting Pub/Sub listener at Django startup...")
            start_pubsub_listener()
            HomeConfig.pubsub_started = True  # Prevent duplicate listeners