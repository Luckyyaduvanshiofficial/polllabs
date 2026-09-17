from pocketbase import PocketBase
from app.core.config import settings

pb = PocketBase(settings.POCKETBASE_URL)

def get_pb_client() -> PocketBase:
    """Returns initialized PocketBase client."""
    return pb

def get_admin_pb_client() -> PocketBase:
    """
    Returns an authenticated PocketBase client using dev admin credentials.
    """
    if settings.POCKETBASE_ADMIN_EMAIL and settings.POCKETBASE_ADMIN_PASSWORD:
        try:
            if not pb.auth_store.is_valid:
                pb.admins.auth_with_password(
                    settings.POCKETBASE_ADMIN_EMAIL,
                    settings.POCKETBASE_ADMIN_PASSWORD
                )
        except Exception as err:
            print(f"[PocketBase] Admin auth warning: {err}")
    return pb
