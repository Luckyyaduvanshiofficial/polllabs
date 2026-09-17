from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.polls import router as polls_router
from app.api.v1.votes import router as votes_router
from app.api.v1.badges import router as badges_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(polls_router, prefix="/polls", tags=["Polls"])
api_router.include_router(votes_router, prefix="/votes", tags=["Votes"])
api_router.include_router(badges_router, prefix="/badges", tags=["Badges"])
