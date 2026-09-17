from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, ConfigDict
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.services.pocketbase_service import AsyncPocketBaseService

class RootResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    message: str
    docs: str
    version: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    pb_service = AsyncPocketBaseService()
    await pb_service.start()
    app.state.pb_service = pb_service
    yield
    await pb_service.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

class ScopedCORSMiddleware(BaseHTTPMiddleware):
    """
    Implements PRD §4.7 CORS rules:
    - Open to any origin for vote/badge/embed endpoints.
    - Restricted to platform frontend origins for poll management and analytics.
    """
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        path = request.url.path
        method = request.method

        if method == "OPTIONS":
            response = Response(status_code=204)
        else:
            response = await call_next(request)

        # Public/embed surfaces: votes, badges, health, and public GET endpoints
        is_public_embed = (
            "/votes" in path
            or "/badges" in path
            or "/health" in path
            or (method == "GET" and "/polls" in path)
            or (method == "GET" and "/leaderboard" in path)
        )

        if is_public_embed:
            # Under W3C Fetch standard, credentials: 'include' requires reflecting the request origin;
            # wildcard '*' with credentials is blocked by browsers.
            if origin:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
            else:
                response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, X-Device-Token"
        elif origin and origin in settings.BACKEND_CORS_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, X-Device-Token"

        return response

app.add_middleware(ScopedCORSMiddleware)
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", response_model=RootResponse)
def root() -> RootResponse:
    return RootResponse(
        message="Welcome to Polls Lab API",
        docs="/docs",
        version=settings.VERSION,
    )
