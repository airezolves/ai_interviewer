"""Kit generation orchestrator — coordinates between services."""

import httpx

from shared.utils.logger import get_logger
from shared.middleware.error_handler import ServiceException
from services.kit_manager.config.settings import get_kit_manager_settings

logger = get_logger(__name__)
settings = get_kit_manager_settings()


class KitOrchestrator:
    """Orchestrates kit generation across AI Engine service."""

    def __init__(self):
        self.ai_engine_url = settings.AI_ENGINE_URL
        self.timeout = httpx.Timeout(120.0)  # 2 min timeout for full kit generation

    async def generate_kit(self, jd_text: str, resume_data: dict, role_type: str) -> dict:
        """Call AI Engine to generate a full kit."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.ai_engine_url}/ai/generate-kit-full",
                    json={
                        "jd_text": jd_text,
                        "resume_data": resume_data,
                        "role_type": role_type,
                    },
                )
                response.raise_for_status()
                result = response.json()

                if result.get("success"):
                    return result["data"]
                else:
                    raise ServiceException(
                        result.get("error", "AI Engine returned an error"),
                        status_code=500,
                    )

            except httpx.TimeoutException:
                logger.error("ai_engine_timeout")
                raise ServiceException("Kit generation timed out. Please try again.", status_code=504)

            except httpx.HTTPStatusError as e:
                logger.error("ai_engine_http_error", status=e.response.status_code)
                raise ServiceException(f"AI Engine error: {e.response.status_code}", status_code=502)

            except Exception as e:
                logger.error("ai_engine_connection_error", error=str(e))
                raise ServiceException(f"Could not connect to AI Engine: {e}", status_code=503)
