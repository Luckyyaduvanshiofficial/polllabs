from pocketbase import PocketBase
from app.core.config import settings

pb = PocketBase(settings.POCKETBASE_URL)

def get_pb_client() -> PocketBase:
    """Returns initialized PocketBase client."""
    return pb
