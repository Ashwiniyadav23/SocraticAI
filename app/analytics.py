import logging
from posthog import Posthog
from app.config import settings

logger = logging.getLogger("analytics")

posthog_client = None

if getattr(settings, "POSTHOG_API_KEY", None):
    posthog_client = Posthog(
        settings.POSTHOG_API_KEY, 
        host=getattr(settings, "POSTHOG_HOST", "https://app.posthog.com")
    )

def capture_event(user_id: str, event_name: str, properties: dict = None):
    """Captures an analytics event and sends it to PostHog if configured."""
    if properties is None:
        properties = {}
        
    logger.info(f"Analytics Event [{event_name}] for User [{user_id}]: {properties}")
    
    if posthog_client:
        try:
            posthog_client.capture(user_id, event=event_name, properties=properties)
        except Exception as e:
            logger.error(f"Failed to send event to PostHog: {e}")
