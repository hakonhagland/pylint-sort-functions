"""FastAPI application with decorator exclusion testing."""

from fastapi import FastAPI

app = FastAPI()


# These decorated endpoints should be excluded from sorting
@app.post("/users/{user_id}/items")
async def create_user_item(user_id: int):
    """Create item for user."""
    return {"user_id": user_id, "item": "created"}


@app.get("/users/{user_id}/items")
async def get_user_items(user_id: int):
    """Get items for user."""
    return {"user_id": user_id, "items": []}


@app.get("/users")
async def list_users():
    """List all users."""
    return {"users": []}


@app.middleware("http")
async def logging_middleware(request, call_next):
    """Logging middleware."""
    response = await call_next(request)
    return response


# These regular functions should trigger sorting violations
async def zebra_async_helper():
    """Async helper function out of order."""
    return "zebra"


async def alpha_async_helper():
    """Should come before zebra_async_helper."""
    return "alpha"


def zebra_sync_helper():
    """Sync helper out of order."""
    return "zebra"


def alpha_sync_helper():
    """Should come before zebra_sync_helper."""
    return "alpha"


class APIService:
    """Service class with method sorting issues."""

    async def zebra_service(self):
        """Service method out of order."""
        return "zebra"

    async def alpha_service(self):
        """Should come before zebra_service."""
        return "alpha"
