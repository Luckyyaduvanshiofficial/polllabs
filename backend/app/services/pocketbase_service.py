import logging
import re
from datetime import datetime, timezone
from typing import Any
from fastapi import Request
import httpx
from app.core.config import settings

logger = logging.getLogger("polls-lab.pocketbase")

# One timeout for every PocketBase call; the two constructors below must agree.
REQUEST_TIMEOUT_SECONDS = 10.0

def sanitize_identifier(value: str) -> str:
    """Sanitizes alphanumeric IDs to prevent filter expression tampering."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "", value)


# Fields a client may sort polls by. Anything else is ignored rather than passed
# through to PocketBase, which would otherwise accept arbitrary sort expressions.
SORTABLE_POLL_FIELDS = frozenset({"created", "updated", "total_votes", "title", "close_at"})
DEFAULT_POLL_SORT = "-created"


def sanitize_sort_expr(value: str, allowed: frozenset[str], default: str) -> str:
    """
    Validates a comma-separated sort expression against a field whitelist,
    preserving PocketBase's leading '-' for descending order.
    """
    if not value:
        return default
    clean_terms: list[str] = []
    for term in value.split(","):
        term = term.strip()
        if not term:
            continue
        descending = term.startswith("-")
        field = term.lstrip("+-")
        if field in allowed:
            clean_terms.append(f"-{field}" if descending else field)
    return ",".join(clean_terms) if clean_terms else default

class AsyncPocketBaseService:
    def __init__(self, base_url: str = settings.POCKETBASE_URL):
        self.base_url = base_url.rstrip("/")
        self.admin_token: str | None = None
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """Initializes long-lived HTTP client for connection pooling."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=REQUEST_TIMEOUT_SECONDS)

    async def close(self) -> None:
        """Gracefully closes long-lived HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Returns active client instance, lazily initializing if not started or if event loop changed."""
        import asyncio
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if (
            self._client is None
            or self._client.is_closed
            or getattr(self, "_loop", None) != current_loop
        ):
            self._loop = current_loop
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=REQUEST_TIMEOUT_SECONDS)
        return self._client

    async def get_admin_token(self) -> str:
        """Retrieves or refreshes superuser auth token for server-side queries."""
        if self.admin_token:
            return self.admin_token

        try:
            client = await self._get_client()
            resp = await client.post(
                "/api/admins/auth-with-password",
                json={
                    "identity": settings.POCKETBASE_ADMIN_EMAIL,
                    "password": settings.POCKETBASE_ADMIN_PASSWORD,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                self.admin_token = data.get("token", "")
                return self.admin_token
        except Exception as err:
            logger.warning("PocketBase admin auth failed: %s", err)

        return ""

    async def _request(
        self,
        method: str,
        path: str,
        user_token: str | None = None,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response | None:
        """Executes an authenticated async HTTP request to PocketBase with connection pooling."""
        token = user_token or await self.get_admin_token()
        headers = {}
        if token:
            headers["Authorization"] = token

        try:
            client = await self._get_client()
            return await client.request(
                method,
                path,
                headers=headers,
                json=json_data,
                params=params,
            )
        except Exception as err:
            logger.warning("PocketBase request error [%s %s]: %s", method, path, err)
            return None

    async def verify_user_token(self, token: str) -> str | None:
        """
        Verifies an auth token with PocketBase and returns the authenticated
        user id, or None when the token is invalid or expired.

        The token payload is NOT trusted: PocketBase re-signs and re-checks it
        via auth-refresh, so a forged or unsigned JWT cannot establish identity.
        """
        if not token:
            return None
        try:
            client = await self._get_client()
            resp = await client.post(
                "/api/collections/users/auth-refresh",
                headers={"Authorization": token},
            )
        except Exception as err:
            logger.warning("Token verification request failed: %s", err)
            return None

        if resp.status_code != 200:
            return None
        record = resp.json().get("record") or {}
        return record.get("id") or None

    # --- Polls CRUD ---

    async def list_polls(
        self,
        page: int = 1,
        per_page: int = 30,
        filter_expr: str = "",
        sort_expr: str = "-created",
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "page": page,
            "perPage": per_page,
            "sort": sort_expr,
        }
        if filter_expr:
            params["filter"] = filter_expr

        resp = await self._request("GET", "/api/collections/polls/records", params=params)
        if resp and resp.status_code == 200:
            return resp.json()
        return {"items": [], "totalItems": 0, "page": page, "perPage": per_page, "totalPages": 1}

    async def get_poll(self, poll_id: str) -> dict[str, Any] | None:
        clean_id = sanitize_identifier(poll_id)
        resp = await self._request("GET", f"/api/collections/polls/records/{clean_id}")
        if resp and resp.status_code == 200:
            return resp.json()
        return None

    async def create_poll(self, poll_data: dict[str, Any], user_token: str | None = None) -> dict[str, Any]:
        resp = await self._request(
            "POST",
            "/api/collections/polls/records",
            user_token=user_token,
            json_data=poll_data,
        )
        if not resp or resp.status_code not in (200, 201):
            detail = resp.text if resp else "Database unreachable"
            raise ValueError(detail)
        return resp.json()

    async def update_poll(
        self, poll_id: str, update_data: dict[str, Any], user_token: str | None = None
    ) -> dict[str, Any]:
        clean_id = sanitize_identifier(poll_id)
        resp = await self._request(
            "PATCH",
            f"/api/collections/polls/records/{clean_id}",
            user_token=user_token,
            json_data=update_data,
        )
        if not resp or resp.status_code != 200:
            detail = resp.text if resp else "Database unreachable"
            raise ValueError(detail)
        return resp.json()

    async def delete_poll(self, poll_id: str, user_token: str | None = None) -> bool:
        clean_id = sanitize_identifier(poll_id)
        resp = await self._request(
            "DELETE",
            f"/api/collections/polls/records/{clean_id}",
            user_token=user_token,
        )
        return bool(resp and resp.status_code == 204)

    # --- Votes CRUD ---

    async def get_existing_vote(self, poll_id: str, device_token: str) -> dict[str, Any] | None:
        """Returns the existing vote record for a device on a poll, or None."""
        clean_poll_id = sanitize_identifier(poll_id)
        clean_token = sanitize_identifier(device_token)
        filter_expr = f'poll_id="{clean_poll_id}" && device_token="{clean_token}"'

        resp = await self._request(
            "GET",
            "/api/collections/votes/records",
            params={"filter": filter_expr, "perPage": 1},
        )
        if resp and resp.status_code == 200:
            items = resp.json().get("items", [])
            return items[0] if items else None
        return None

    async def cast_vote(self, vote_data: dict[str, Any]) -> dict[str, Any]:
        resp = await self._request(
            "POST",
            "/api/collections/votes/records",
            json_data=vote_data,
        )
        if not resp or resp.status_code not in (200, 201):
            detail = resp.text if resp else "Database unreachable"
            raise ValueError(detail)
        return resp.json()

    async def update_vote(self, vote_id: str, vote_data: dict[str, Any]) -> dict[str, Any]:
        """Updates an existing vote record in place (multi-select selection changes)."""
        clean_id = sanitize_identifier(vote_id)
        resp = await self._request(
            "PATCH",
            f"/api/collections/votes/records/{clean_id}",
            json_data=vote_data,
        )
        if not resp or resp.status_code != 200:
            detail = resp.text if resp else "Database unreachable"
            raise ValueError(detail)
        return resp.json()

    async def record_vote_and_increment(
        self,
        poll_id: str,
        vote_data: dict[str, Any],
        existing_vote_id: str | None = None,
        newly_counted_ids: list[str] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Records a vote and increments poll counters in PocketBase.
        Handles both single-choice (str) and multi-select (list) option_id values.

        `existing_vote_id` updates that record instead of inserting a new one and
        suppresses the total_votes increment, so a device counts once per poll.
        `newly_counted_ids` limits option increments to options not already
        counted for this device.
        """
        poll = await self.get_poll(poll_id)
        if not poll:
            raise ValueError("Poll not found")

        # Normalize option_id to a list for uniform handling
        raw_option_id = vote_data["option_id"]
        option_ids = raw_option_id if isinstance(raw_option_id, list) else [raw_option_id]

        # Options whose counts change. On a repeat multi-select vote only the
        # newly added options are counted, and the device is not counted toward
        # total_votes a second time — otherwise revisiting a poll inflates both.
        increment_ids = list(option_ids) if newly_counted_ids is None else list(newly_counted_ids)

        # 1. Record the vote: update the device's existing record in place when
        # it has one, so a device holds exactly one vote row per poll.
        if existing_vote_id:
            vote_resp = await self.update_vote(existing_vote_id, vote_data)
        else:
            vote_resp = await self.cast_vote(vote_data)

        # 2. Update option-specific counts and atomically increment total_votes
        options = poll.get("options", [])
        for oid in increment_ids:
            for opt in options:
                if opt.get("id") == oid:
                    opt["vote_count"] = opt.get("vote_count", 0) + 1
                    break

        update_payload: dict[str, Any] = {"options": options}
        counts_new_voter = existing_vote_id is None
        if counts_new_voter:
            update_payload["total_votes+"] = 1

        updated_poll = await self.update_poll(poll_id, update_payload)
        # Ensure returned poll reflects latest total_votes for display mapping
        if counts_new_voter and (
            "total_votes" not in updated_poll
            or updated_poll["total_votes"] == poll.get("total_votes", 0)
        ):
            updated_poll["total_votes"] = poll.get("total_votes", 0) + 1
        return vote_resp, updated_poll

    async def list_votes_for_poll(self, poll_id: str) -> list[dict[str, Any]]:
        """Fetches all votes for a poll with automatic pagination (PRD §5)."""
        clean_poll_id = sanitize_identifier(poll_id)
        filter_expr = f'poll_id="{clean_poll_id}"'
        all_votes: list[dict[str, Any]] = []
        page = 1
        per_page = 200

        while True:
            resp = await self._request(
                "GET",
                "/api/collections/votes/records",
                params={"filter": filter_expr, "page": page, "perPage": per_page},
            )
            if not resp or resp.status_code != 200:
                break

            data = resp.json()
            items = data.get("items", [])
            all_votes.extend(items)

            total_pages = data.get("totalPages", 1)
            if page >= total_pages or len(items) == 0:
                break
            page += 1

        return all_votes

    # --- Abuse Reports CRUD ---

    async def record_abuse_report(
        self,
        poll_id: str,
        reason: str,
        ip_hash: str,
    ) -> dict[str, Any]:
        """Persists an abuse report for a poll in PocketBase (PRD §4.6)."""
        clean_poll_id = sanitize_identifier(poll_id)
        report_data = {
            "poll_id": clean_poll_id,
            "reason": reason,
            "ip_hash": ip_hash,
        }
        resp = await self._request(
            "POST",
            "/api/collections/abuse_reports/records",
            json_data=report_data,
        )
        if resp and resp.status_code in (200, 201):
            return resp.json()
        return report_data

    # --- Poll Images (Phase 4 file storage) ---

    async def upload_image_record(
        self,
        data: dict[str, Any],
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict[str, Any] | None:
        """Creates a poll_images record with a file upload (multipart, admin token)."""
        token = await self.get_admin_token()
        headers = {"Authorization": token} if token else {}
        try:
            client = await self._get_client()
            resp = await client.post(
                "/api/collections/poll_images/records",
                headers=headers,
                data=data,
                files={"image": (filename, content, content_type)},
            )
            if resp.status_code in (200, 201):
                return resp.json()
            logger.warning("Image record create failed [%s]: %s", resp.status_code, resp.text[:200])
        except Exception as err:
            logger.warning("Image upload request error: %s", err)
        return None

    async def list_image_records_older_than(self, cutoff_iso: str, per_page: int = 100) -> list[dict[str, Any]]:
        """Lists poll_images records created before cutoff (for orphan cleanup)."""
        resp = await self._request(
            "GET",
            "/api/collections/poll_images/records",
            params={"filter": f'created < "{cutoff_iso}"', "perPage": per_page, "sort": "created"},
        )
        if resp and resp.status_code == 200:
            return resp.json().get("items", [])
        return []

    async def delete_image_record(self, record_id: str) -> bool:
        """Deletes a poll_images record and its stored file."""
        clean_id = sanitize_identifier(record_id)
        resp = await self._request("DELETE", f"/api/collections/poll_images/records/{clean_id}")
        return bool(resp and resp.status_code == 204)

    # --- User Lifecycle & Deletion ---

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        """Returns a user record, or None when it is missing."""
        clean_id = sanitize_identifier(user_id)
        resp = await self._request("GET", f"/api/collections/users/records/{clean_id}")
        if resp and resp.status_code == 200:
            return resp.json()
        return None

    async def set_user_deletion_status(
        self,
        user_id: str,
        status: str,
        scheduled_for: str | None = None,
    ) -> dict[str, Any]:
        """Sets deletion lifecycle status on a user record (PRD §7)."""
        clean_user_id = sanitize_identifier(user_id)
        payload: dict[str, Any] = {"deletion_status": status}
        if scheduled_for is not None:
            payload["deletion_scheduled_for"] = scheduled_for

        resp = await self._request(
            "PATCH",
            f"/api/collections/users/records/{clean_user_id}",
            json_data=payload,
        )
        if resp and resp.status_code == 200:
            return resp.json()
        return {"id": user_id, "deletion_status": status}

    async def purge_expired_accounts(self) -> int:
        """Purges accounts that reached the end of their 7-day deletion grace window (PRD §7)."""
        now_iso = datetime.now(timezone.utc).isoformat()
        filter_expr = f'deletion_status="pending_deletion" && deletion_scheduled_for<="{now_iso}"'
        resp = await self._request(
            "GET",
            "/api/collections/users/records",
            params={"filter": filter_expr, "perPage": 100},
        )
        if not resp or resp.status_code != 200:
            return 0

        users = resp.json().get("items", [])
        purged = 0
        for u in users:
            # polls.owner is not a cascading relation, so owned polls are removed
            # explicitly first. Deleting a poll cascades to its votes, abuse
            # reports and images. Without this the user row disappears and the
            # polls survive as orphans (PRD §7).
            await self.delete_polls_owned_by(u["id"])
            del_resp = await self._request("DELETE", f"/api/collections/users/records/{u['id']}")
            if del_resp and del_resp.status_code == 204:
                purged += 1
        return purged

    async def delete_polls_owned_by(self, user_id: str) -> int:
        """Deletes every poll owned by a user, cascading to votes and reports."""
        clean_user_id = sanitize_identifier(user_id)
        deleted = 0
        while True:
            resp = await self._request(
                "GET",
                "/api/collections/polls/records",
                params={"filter": f'owner="{clean_user_id}"', "perPage": 100},
            )
            if not resp or resp.status_code != 200:
                return deleted
            items = resp.json().get("items", [])
            if not items:
                return deleted
            for poll in items:
                if await self.delete_poll(poll["id"]):
                    deleted += 1
            if len(items) < 100:
                return deleted

def get_pb_service(request: Request) -> AsyncPocketBaseService:
    """FastAPI dependency yielding async PocketBase service managed on application state."""
    pb = getattr(request.app.state, "pb_service", None)
    if pb is None:
        pb = AsyncPocketBaseService()
        request.app.state.pb_service = pb
    return pb
