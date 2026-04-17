# Name Profile API

A FastAPI REST API that enriches a name with gender, age, and nationality predictions by integrating [Genderize.io](https://genderize.io), [Agify.io](https://agify.io), and [Nationalize.io](https://nationalize.io).

## Base URL
```
https://profile-app-00443e51.fastapicloud.dev  
```

---

## Endpoints

### `POST /api/profiles/`
Create a new profile from a name. If the name already exists, returns the existing profile.

**Request Body**
```json
{ "name": "ella" }
```

**Response `201 Created`**
```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.98,
    "sample_size": 1234,
    "age": 34,
    "age_group": "adult",
    "country_id": "NG",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

**Response `200 OK`** *(name already exists)*
```json
{
  "status": "success",
  "message": "Profile already exists",
  "data": { "...existing profile..." }
}
```

---

### `GET /api/profiles/`
Retrieve all profiles. Supports optional filters.

**Query Parameters**

| Parameter    | Type   | Example           |
|--------------|--------|-------------------|
| `gender`     | string | `?gender=female`  |
| `country_id` | string | `?country_id=NG`  |
| `age_group`  | string | `?age_group=adult`|

**Response `200 OK`**
```json
{
  "status": "success",
  "count": 2,
  "data": [ { "...profile..." } ]
}
```

---

### `GET /api/profiles/{id}`
Retrieve a single profile by ID.

**Response `200 OK`**
```json
{
  "status": "success",
  "data": { "...profile..." }
}
```

---

### `DELETE /api/profiles/{id}`
Delete a profile by ID.

**Response `204 No Content`**

---

## Age Groups

| Range | Group    |
|-------|----------|
| 0–12  | child    |
| 13–19 | teenager |
| 20–59 | adult    |
| 60+   | senior   |

---

## Error Responses

All errors follow this structure:
```json
{
  "status": "error",
  "message": "<error message>"
}
```

| Status | Reason |
|--------|--------|
| `400`  | Missing or empty name |
| `404`  | Profile not found |
| `502`  | Upstream API returned no prediction |

---

## Running Locally

### Prerequisites
- Python 3.10+

### Setup
```bash
git clone https://github.com/bnabdulwasiu/HNG.git
cd your-repo

python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
fastapi dev main.py
```

API runs at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

---

## Deployment

Deployed on [FastAPI Cloud](https://fastapicloud.com):
```bash
fastapi deploy main.py
```

---

## Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/) — web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) + [aiosqlite](https://aiosqlite.omnilib.dev/) — async SQLite
- [httpx](https://www.python-httpx.org/) — async HTTP client
- [uuid6](https://github.com/oittaa/uuid6-python) — UUID v7 generation
- [Genderize.io](https://genderize.io) — gender prediction
- [Agify.io](https://agify.io) — age prediction
- [Nationalize.io](https://nationalize.io) — nationality prediction
