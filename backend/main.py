from typing import Annotated

from celery.result import AsyncResult
from fastapi import (
    Body,
    Depends,
    FastAPI,
    Form,
    Request
)
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from worker import create_task
from backend.apis.v1 import router_v1
from backend.core.database import get_db
from backend.models.v1.users import User
from backend.utils.users import get_current_active_user


app = FastAPI()
app.include_router(router_v1, prefix="/api/v1")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

    
@app.get("/")
async def root(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return {"messasge": "Welcome to the server"}


# @app.post("/tasks", status_code=201)  
# def run_task(payload = Body(...)):
#     task_type = payload["type"]
#     task = create_task.delay(int(task_type))
#     return JSONResponse({"task_id": task.id})


# @app.get("/tasks/{task_id}")
# def get_status(task_id):
#     task_result = AsyncResult(task_id)
#     result = {
#         "task_id": task_id,
#         "task_status": task_result.status,
#         "task_result": task_result.result
#     }
#     return JSONResponse(result)
