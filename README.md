# Gender Classifier API

A FastAPI-based REST API that predicts the gender of a name using the [Genderize.io](https://genderize.io) API.

## Endpoint

### `GET /api/classify`

Classifies the gender of a given name.

**Query Parameters**

| Parameter | Type   | Required | Description            |
|-----------|--------|----------|------------------------|
| `name`    | string | Yes      | The name to classify   |

**Example Request**
```
GET /api/classify?name=john
```

**Success Response `200 OK`**
```json
{
  "status": "success",
  "data": {
    "name": "john",
    "gender": "male",
    "probability": 0.99,
    "sample_size": 1234,
    "is_confident": true,
    "processed_at": "2026-04-01T12:00:00Z"
  }
}
```

**Error Responses**

| Status | Description |
|--------|-------------|
| `400`  | Missing or empty name parameter |
| `422`  | Name is not a string / No prediction available for the provided name |
| `500/502` | Upstream or server failure |

All errors follow this structure:
```json
{
  "status": "error",
  "message": "<error message>"
}
```

---

## Running Locally

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/Bnabdulwasiu/gender-classifier
cd gender-classifier

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Start the server

```bash
fastapi dev main.py
```

The API will be available at `http://localhost:8000`

Interactive docs available at `http://localhost:8000/docs`

---

## Deployment

This API is deployed on [FastAPI Cloud](https://gender-classfier.fastapicloud.dev/api/classify).

```bash
fastapi deploy main.py
```

---

## Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/) — web framework
- [httpx](https://www.python-httpx.org/) — async HTTP client
- [Pydantic](https://docs.pydantic.dev/) — data validation
- [Genderize.io](https://genderize.io) — gender prediction API
