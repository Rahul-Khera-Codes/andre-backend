from fastapi import APIRouter

from .auth import auth_router_v1

router_v1 = APIRouter()
router_v1.include_router(auth_router_v1)