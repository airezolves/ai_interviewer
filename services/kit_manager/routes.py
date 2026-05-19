"""Kit Manager service routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.connector import get_db
from shared.schemas.common import APIResponse, HealthResponse
from services.kit_manager.schemas import (
    CreateKitRequest,
    KitSummary,
    KitDetail,
    KitStatusResponse,
    FeedbackRequest,
    ShareLinkResponse,
)
from services.kit_manager.service import KitManagerService
from services.kit_manager.orchestrator import KitOrchestrator
from services.kit_manager.config.settings import get_kit_manager_settings

settings = get_kit_manager_settings()
router = APIRouter(prefix="/kits", tags=["kits"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(service="kit_manager")


@router.post("", response_model=APIResponse[KitStatusResponse])
async def create_kit(
    request: CreateKitRequest,
    background_tasks: BackgroundTasks,
    user_id: str = "anonymous",
    db: AsyncSession = Depends(get_db),
):
    """Create a new interview kit. Triggers async generation."""
    service = KitManagerService(db)
    kit = await service.create_kit(UUID(user_id) if user_id != "anonymous" else UUID(int=0), request)

    # Trigger async generation
    background_tasks.add_task(
        _generate_kit_background,
        kit_id=kit.id,
        jd_text=request.jd_text,
        resume_data=request.resume_data,
        role_type=request.role_type,
    )

    return APIResponse(
        data=KitStatusResponse(
            kit_id=kit.id,
            status="generating",
            progress=0,
            message="Kit generation started",
        )
    )


async def _generate_kit_background(
    kit_id: UUID, jd_text: str, resume_data: dict, role_type: str
):
    """Background task to generate kit via AI Engine."""
    from shared.database.connector import get_db_context

    orchestrator = KitOrchestrator()

    try:
        generated_kit = await orchestrator.generate_kit(jd_text, resume_data, role_type)

        async with get_db_context() as db:
            service = KitManagerService(db)
            await service.store_kit_result(kit_id, generated_kit)

    except Exception as e:
        async with get_db_context() as db:
            service = KitManagerService(db)
            await service.mark_kit_failed(kit_id, str(e))


@router.get("", response_model=APIResponse[list[KitSummary]])
async def list_kits(
    page: int = 1,
    page_size: int = 20,
    user_id: str = "anonymous",
    db: AsyncSession = Depends(get_db),
):
    """List user's interview kits."""
    service = KitManagerService(db)
    uid = UUID(user_id) if user_id != "anonymous" else UUID(int=0)
    kits = await service.list_kits(uid, page, page_size)
    return APIResponse(data=kits)


@router.get("/{kit_id}", response_model=APIResponse[KitDetail])
async def get_kit(
    kit_id: UUID,
    user_id: str = "anonymous",
    db: AsyncSession = Depends(get_db),
):
    """Get full interview kit with all sections."""
    service = KitManagerService(db)
    uid = UUID(user_id) if user_id != "anonymous" else None
    kit = await service.get_kit(kit_id, uid)
    return APIResponse(data=kit)


@router.get("/{kit_id}/status", response_model=APIResponse[KitStatusResponse])
async def get_kit_status(
    kit_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Check kit generation status."""
    service = KitManagerService(db)
    kit = await service.get_kit(kit_id)
    progress = 100 if kit.status == "completed" else (50 if kit.status == "generating" else 0)
    return APIResponse(
        data=KitStatusResponse(
            kit_id=kit_id,
            status=kit.status,
            progress=progress,
        )
    )


@router.delete("/{kit_id}")
async def delete_kit(
    kit_id: UUID,
    user_id: str = "anonymous",
    db: AsyncSession = Depends(get_db),
):
    """Delete an interview kit."""
    service = KitManagerService(db)
    uid = UUID(user_id) if user_id != "anonymous" else UUID(int=0)
    await service.delete_kit(kit_id, uid)
    return APIResponse(message="Kit deleted")


@router.post("/{kit_id}/share", response_model=APIResponse[ShareLinkResponse])
async def share_kit(
    kit_id: UUID,
    user_id: str = "anonymous",
    db: AsyncSession = Depends(get_db),
):
    """Generate a shareable link for a kit."""
    service = KitManagerService(db)
    uid = UUID(user_id) if user_id != "anonymous" else UUID(int=0)
    token = await service.generate_share_link(kit_id, uid)

    share_url = f"{settings.FRONTEND_URL}/shared/{token}"
    return APIResponse(data=ShareLinkResponse(share_url=share_url))


@router.get("/shared/{token}", response_model=APIResponse[KitDetail])
async def get_shared_kit(token: str, db: AsyncSession = Depends(get_db)):
    """Access a shared kit (public)."""
    service = KitManagerService(db)
    kit = await service.get_shared_kit(token)
    return APIResponse(data=kit)


@router.post("/{kit_id}/feedback")
async def submit_feedback(
    kit_id: UUID,
    request: FeedbackRequest,
    user_id: str = "anonymous",
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback on a kit."""
    service = KitManagerService(db)
    uid = UUID(user_id) if user_id != "anonymous" else UUID(int=0)
    await service.submit_feedback(kit_id, uid, request)
    return APIResponse(message="Feedback submitted")
