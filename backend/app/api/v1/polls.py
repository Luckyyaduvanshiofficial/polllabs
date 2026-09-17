from fastapi import APIRouter, HTTPException, status
from app.schemas.poll import PollCreate, PollResponse

router = APIRouter(prefix="/polls", tags=["Polls"])

@router.get("/", response_model=dict)
async def list_public_polls() -> dict:
    """Lists discoverable public polls."""
    return {"polls": []}

@router.get("/{poll_id}")
async def get_poll(poll_id: str) -> dict:
    """Retrieves a single poll by ID."""
    return {
        "id": poll_id,
        "title": "Sample Poll",
        "options": [
            {"id": "opt-1", "text": "Option A", "vote_count": 0},
            {"id": "opt-2", "text": "Option B", "vote_count": 0}
        ],
        "visibility": "public",
        "result_display": "show_counts"
    }

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_poll(poll: PollCreate) -> dict:
    """Creates a new poll (requires GitHub OAuth sign-in)."""
    return {"id": "poll_placeholder", "message": "Poll created successfully"}
