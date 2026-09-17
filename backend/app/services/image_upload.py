"""Phase 4: poll option image validation and storage helpers.

Uploads are JPEG/PNG/GIF/WebP only, capped at 2MB, verified by magic
bytes (not client-supplied content types). Files live in the PocketBase
`poll_images` collection, so local-disk and S3 storage backends both work
transparently behind the same /api/files/... URLs.
"""

import logging
import re
from urllib.parse import quote

from app.core.config import settings

logger = logging.getLogger("polllabs.images")

MAX_IMAGE_BYTES = 2 * 1024 * 1024
ALLOWED_MIME_TYPES = ("image/jpeg", "image/png", "image/gif", "image/webp")
STAGED_ORPHAN_MAX_AGE_HOURS = 24


def detect_image_mime(head: bytes) -> str | None:
    """Sniffs image type from magic bytes. Returns None for non-images."""
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        return "image/gif"
    if len(head) >= 12 and head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "image/webp"
    return None


def sanitize_filename(name: str | None) -> str:
    """Strips paths and unsafe chars from an upload filename."""
    base = (name or "upload").split("/")[-1].split("\\")[-1]
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", base).strip("._") or "upload"
    return safe[:100]


def build_file_url(collection: str, record_id: str, filename: str) -> str:
    """Public file URL served by PocketBase (local disk or S3 alike)."""
    base = settings.POCKETBASE_URL.rstrip("/")
    clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "", record_id)
    return f"{base}/api/files/{collection}/{clean_id}/{quote(filename)}"
