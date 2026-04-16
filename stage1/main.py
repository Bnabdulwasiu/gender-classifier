from datetime import datetime, timezone
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException, Request, Path, status, Response
import httpx
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import asyncio


# Database Setup
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Float, Integer
import uuid
from sqlalchemy import select

DATABASE_URL = "sqlite+aiosqlite:///./profiles.db"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    gender = Column(String, nullable=True)
    gender_probability = Column(Float, nullable=True)
    sample_size = Column(Integer, nullable=True)
    age = Column(Integer, nullable=True)
    age_group = Column(String, nullable=True)
    country_id = Column(String, nullable=True)
    country_probability = Column(Float, nullable=True)
    created_at = Column(String)

class ProfileSchema(BaseModel):
    id: str
    name: str
    gender: str
    age: int
    age_group: str
    country_id: str

    class Config:
        from_attributes = True

class ProfileListResponse(BaseModel):
    status: str = "success"
    count: int
    data: List[ProfileSchema]

class CreateProfileRequest(BaseModel):
    name: str

#Helper functions
def error_response(status_code: int, message: str):
     raise HTTPException(
          status_code=status_code,
          detail={
               "status": "error",
               "message": message
          }
     )


def get_age_group(age: int | None) -> str | None:
    if age is None:
        return None
    if age <= 12:
        return "child"
    elif age <= 19:
        return "teenager"
    elif age <= 59:
        return "adult"
    else:
        return "senior"


@asynccontextmanager
async def lifespan(app: FastAPI):
    #Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.state.genderize = httpx.AsyncClient(base_url="https://api.genderize.io", timeout=10.0)
    app.state.agify = httpx.AsyncClient(base_url="https://api.agify.io", timeout=10.0)
    app.state.nationalize = httpx.AsyncClient(base_url="https://api.nationalize.io", timeout=10.0)
    yield
    await asyncio.gather(

        app.state.genderize.aclose(),
        app.state.agify.aclose(),
        app.state.nationalize.aclose(),

    )


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
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

def _profile_to_dict(profile: Profile) -> dict:
    return {
        "id": profile.id,
        "name": profile.name,
        "gender": profile.gender,
        "gender_probability": profile.gender_probability,
        "sample_size": profile.sample_size,
        "age": profile.age,
        "age_group": profile.age_group,
        "country_id": profile.country_id,
        "country_probability": profile.country_probability,
        "created_at": profile.created_at,
    }


# Post function
@app.post("/api/profiles", status_code=201)
async def create_profile(body: CreateProfileRequest):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail={
            "status": "error",
            "message": "Missing or empty name"
        })

    async with AsyncSessionLocal() as session:
        # Check if profile already exists
        result = await session.execute(select(Profile).where(Profile.name == name.lower()))
        existing = result.scalar_one_or_none()

        if existing:
            return JSONResponse(status_code=200, content={
                "status": "success",
                "message": "Profile already exists",
                "data": _profile_to_dict(existing)
            })

        # Fetch all 3 APIs concurrently
        try:
            gender_res, age_res, nation_res = await asyncio.gather(
                app.state.genderize.get("/", params={"name": name}),
                app.state.agify.get("/", params={"name": name}),
                app.state.nationalize.get("/", params={"name": name}),
            )
        except (httpx.HTTPStatusError, httpx.RequestError):
            raise HTTPException(status_code=502, detail={
                "status": "error",
                "message": "Upstream or server failure"
            })

        gender_data = gender_res.json()
        age_data = age_res.json()
        nation_data = nation_res.json()

        # Pick top country by probability
        countries = nation_data.get("country", [])
        top_country = max(countries, key=lambda c: c["probability"]) if countries else None

        created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        profile = Profile(
            id=str(uuid.uuid4()),
            name=name.lower(),
            gender=gender_data.get("gender"),
            gender_probability=gender_data.get("probability"),
            sample_size=gender_data.get("count"),
            age=age_data.get("age"),
            age_group=get_age_group(age_data.get("age")),
            country_id=top_country["country_id"] if top_country else None,
            country_probability=top_country["probability"] if top_country else None,
            created_at=created_at,
        )

        session.add(profile)
        await session.commit()

        return JSONResponse(status_code=201, content={
            "status": "success",
            "data": _profile_to_dict(profile)
        })
    

@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Profile).where(Profile.id == profile_id))
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(status_code=404, detail={
                "status": "error",
                "message": "Profile not found"
            })

        return {"status": "success", "data": _profile_to_dict(profile)}


@app.get("/api/profiles/", response_model=ProfileListResponse)
async def get_all_profiles(
    gender: Optional[str] = None,
    country_id: Optional[str] = None,
    age_group: Optional[str] = None  # string not int
):
    async with AsyncSessionLocal() as session:
        query = select(Profile)

        # Apply filters if provided
        if gender:
            query = query.where(Profile.gender == gender.lower())
        if country_id:
            query = query.where(Profile.country_id == country_id.upper())
        if age_group:
            query = query.where(Profile.age_group == age_group.lower())

        result = await session.execute(query)
        profiles = result.scalars().all()

        return {
            "status": "success",
            "count": len(profiles),
            "data": profiles
        }
    

@app.delete("/api/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(profile_id: str):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Profile).where(Profile.id == profile_id))
            profile = result.scalar_one_or_none()

            if not profile:
                raise HTTPException(status_code=404, detail={
                    "status": "error",
                    "message": "Profile not found"
                })
            
            await session.delete(profile)
            await session.commit()

            # 4. Return Response(status_code=204) or simply None
            return Response(status_code=status.HTTP_204_NO_CONTENT)