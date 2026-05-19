"""Gateway routes — proxy to downstream services."""

from fastapi import APIRouter, Request, Depends, Header
from fastapi.responses import JSONResponse
import httpx

from shared.schemas.common import HealthResponse
from shared.utils.security import decode_token
from shared.middleware.error_handler import UnauthorizedException
from services.gateway.config.settings import get_gateway_settings

settings = get_gateway_settings()
router = APIRouter(tags=["gateway"])

# Service URL mapping
SERVICE_MAP = {
    "/api/auth": settings.AUTH_SERVICE_URL,
    "/api/resume": settings.RESUME_PARSER_URL,
    "/api/ai": settings.AI_ENGINE_URL,
    "/api/kits": settings.KIT_MANAGER_URL,
    "/api/pdf": settings.PDF_GENERATOR_URL,
    "/api/billing": settings.BILLING_SERVICE_URL,
}


async def get_optional_user(authorization: str | None = Header(None)) -> dict | None:
    """Extract user from JWT if present."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if payload:
        return {"user_id": payload.get("sub"), "email": payload.get("email"), "plan": payload.get("plan")}
    return None


async def require_auth(authorization: str = Header(...)) -> dict:
    """Require valid JWT token."""
    if not authorization.startswith("Bearer "):
        raise UnauthorizedException()
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise UnauthorizedException("Invalid or expired token")
    return {"user_id": payload["sub"], "email": payload.get("email"), "plan": payload.get("plan")}


@router.get("/health", response_model=HealthResponse)
async def gateway_health():
    return HealthResponse(service="gateway")


@router.get("/api/health")
async def api_health():
    """Aggregated health check across all services."""
    results = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for prefix, url in SERVICE_MAP.items():
            service_name = prefix.split("/")[-1]
            try:
                resp = await client.get(f"{url}/{service_name}/health")
                results[service_name] = "healthy" if resp.status_code == 200 else "unhealthy"
            except Exception:
                results[service_name] = "unreachable"

    all_healthy = all(s == "healthy" for s in results.values())
    return {"status": "healthy" if all_healthy else "degraded", "services": results}


@router.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def proxy(request: Request, path: str):
    """Proxy requests to downstream services."""
    # Determine target service
    full_path = f"/api/{path}"
    target_url = None
    target_prefix = None

    for prefix, url in SERVICE_MAP.items():
        if full_path.startswith(prefix):
            target_url = url
            target_prefix = prefix
            break

    if not target_url:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": f"No service handles path: {full_path}"},
        )

    # Build downstream URL — strip /api prefix
    downstream_path = full_path[len("/api"):]  # e.g., /auth/login, /kits, etc.
    url = f"{target_url}{downstream_path}"

    # Forward the request
    headers = dict(request.headers)
    headers.pop("host", None)

    # Add user context from JWT if present
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        payload = decode_token(token)
        if payload:
            headers["x-user-id"] = payload.get("sub", "")
            headers["x-user-email"] = payload.get("email", "")
            headers["x-user-plan"] = payload.get("plan", "free")

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            body = await request.body()
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                params=request.query_params,
            )

            return JSONResponse(
                status_code=response.status_code,
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else {"data": response.text},
                headers={"x-gateway-forwarded": "true"},
            )

        except httpx.TimeoutException:
            return JSONResponse(
                status_code=504,
                content={"success": False, "error": "Service timeout"},
            )
        except httpx.ConnectError:
            return JSONResponse(
                status_code=503,
                content={"success": False, "error": "Service unavailable"},
            )
