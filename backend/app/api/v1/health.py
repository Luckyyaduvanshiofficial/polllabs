from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", response_model=dict[str, str])
@router.get("/", response_model=dict[str, str])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "polllabs-api"}
