from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.polls import router as polls_router
from app.api.v1.votes import router as votes_router
from app.api.v1.leaderboard import router as leaderboard_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.badges import router as badges_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(polls_router)
api_router.include_router(votes_router)
api_router.include_router(leaderboard_router)
api_router.include_router(analytics_router)
api_router.include_router(badges_router)
