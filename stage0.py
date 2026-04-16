from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, Query, HTTPException, Request
import httpx
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class GenderData(BaseModel):
    name: str
    gender: Optional[str] = None
    probability: float
    sample_size: int
    is_confident: bool
    processed_at: str

class SuccessResponse(BaseModel):
    status: str = "success"
    data: GenderData

class Errorresponse(BaseModel):
    status: str = "error"
    message: str 


def error_response(status_code: int, message: str):
     raise HTTPException(
          status_code=status_code,
          detail={
               "status": "error",
               "message": message
          }
     )


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient(base_url="https://api.genderize.io",
                                         timeout=10.0)
    yield
    await app.state.client.aclose()


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):

    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": str(exc.detail)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "name is not a string"
        }
    )


@app.get("/api/classify", response_model=SuccessResponse)
async def get_gender(name: str = Query(...,
                                    description="The name to be classified",
                                    )):
    
    if name is None or not name.strip():
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "message": "Missing or empty name parameter"
        })


    try:
        response = await app.state.client.get("/", params={"name": name})
        response.raise_for_status()
    
    except (httpx.HTTPStatusError, httpx.RequestError):
        return error_response(502, "Upstream or server failure")

    raw_data = response.json()

    if raw_data.get("gender") is None or raw_data.get("count") == 0:
        return error_response(404, "No prediction for the provided name")
        
    count = raw_data.get("count")
    probability = raw_data.get("probability")
    is_confident = (probability >= 0.7) and (count >= 100)
    processed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    result = GenderData(
        name=raw_data.get("name"),
        gender=raw_data.get("gender"),
        probability=probability,
        sample_size=count,
        is_confident=is_confident,
        processed_at=processed_at,
    )
    
    return SuccessResponse(data=result)
                                                                                                                