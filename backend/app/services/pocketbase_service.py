import logging
import re
from typing import Any
import httpx
from app.core.config import settings

logger = logging.getLogger("polllabs.pocketbase")

def sanitize_identifier(value: str) -> str:
    """Sanitizes alphanumeric IDs to prevent filter expression tampering."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "", value)

class AsyncPocketBaseService:
    def __init__(self, base_url: str = settings.POCKETBASE_URL):
        self.base_url = base_url.rstrip("/")
        self.admin_token: str | None = None

    async def get_admin_token(self) -> str:
        """Retrieves or refreshes superuser auth token for server-side queries."""
        if self.admin_token:
            return self.admin_token

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=2.0) as client:
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
        except httpx.RequestError as err:
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
        """Executes an authenticated async HTTP request to PocketBase with connection failure handling."""
        token = user_token or await self.get_admin_token()
        headers = {}
        if token:
            headers["Authorization"] = token

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=5.0) as client:
                return await client.request(
                    method,
                    path,
                    headers=headers,
                    json=json_data,
                    params=params,
                )
        except httpx.RequestError as err:
            logger.warning("PocketBase request error [%s %s]: %s", method, path, err)
            return None

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

    async def has_device_voted(self, poll_id: str, device_token: str) -> bool:
        """Checks if a device token has already cast a vote for a specific poll with sanitized binding."""
        clean_poll_id = sanitize_identifier(poll_id)
        clean_token = sanitize_identifier(device_token)
        filter_expr = f'poll_id="{clean_poll_id}" && device_token="{clean_token}"'

        resp = await self._request(
            "GET",
            "/api/collections/votes/records",
            params={"filter": filter_expr, "perPage": 1},
        )
        if resp and resp.status_code == 200:
            data = resp.json()
            return data.get("totalItems", 0) > 0
        return False

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

pb_service = AsyncPocketBaseService()

def get_pb_service() -> AsyncPocketBaseService:
    """FastAPI dependency yielding async PocketBase service."""
    return pb_service
