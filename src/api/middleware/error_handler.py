from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except SQLAlchemyError as e:
        return JSONResponse(
            status_code=500,
            content={"message": "Database error", "detail": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error", "detail": str(e)}
        )
