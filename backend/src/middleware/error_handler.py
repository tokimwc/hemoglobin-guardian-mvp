from fastapi import Request, status
from fastapi.responses import JSONResponse
from src.models.error_response import ErrorResponse
import logging

logger = logging.getLogger(__name__)

async def error_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except TimeoutError as e:
        logger.error(f"Timeout error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content=ErrorResponse(
                message="サーバーからの応答がタイムアウトしました。",
                details=str(e),
                fallback_data={
                    "iron_rich_foods": ["ほうれん草", "レバー", "牛肉"],
                    "meal_suggestions": ["鉄分豊富な食事を心がけましょう"],
                    "lifestyle_tips": ["十分な睡眠をとりましょう"]
                }
            ).dict()
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                message="入力データが不正です。",
                details=str(e)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                message="予期せぬエラーが発生しました。",
                details=str(e),
                fallback_data={
                    "iron_rich_foods": ["ほうれん草", "レバー", "牛肉"],
                    "meal_suggestions": ["鉄分豊富な食事を心がけましょう"],
                    "lifestyle_tips": ["十分な睡眠をとりましょう"]
                }
            ).dict()
        ) 