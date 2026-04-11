from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.auth import TokenPayload
from app.schemas.council import CouncilConfigCreate, CouncilConfigResponse, ExecuteRequest, ExecuteResponse
from app.schemas.execution import ExecutionResponse
from app.services import council as council_service

router = APIRouter(prefix="/api/council", tags=["council"])


@router.post("/", response_model=CouncilConfigResponse)
async def create_council(
    body: CouncilConfigCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await council_service.create_council(db, current_user.sub, body)


@router.get("/{council_id}", response_model=CouncilConfigResponse)
async def get_council(
    council_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    config = await council_service.get_council(db, council_id, current_user.sub)
    if not config:
        raise HTTPException(status_code=404, detail="Council not found")
    return config


@router.post("/execute", response_model=ExecuteResponse)
async def execute_council(
    body: ExecuteRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    execution = await council_service.create_execution(db, body, current_user.sub)
    return ExecuteResponse(execution_id=execution.id, status=execution.status)


@router.get("/execution/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    execution = await council_service.get_execution(db, execution_id, current_user.sub)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution
