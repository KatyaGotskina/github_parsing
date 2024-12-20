from fastapi import Request
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, JSONResponse

from core.exceptions import DBError, NotFoundError


class DomainErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            response = await call_next(request)
            return response
        except DBError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"err": "Произошла ошибка при получении данных"},
            )
        except NotFoundError as err:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"err": str(err)}
            )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"err": "Произошла внутренняя ошибка сервера"},
            )
