from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

async def error_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except TimeoutError as e:
        logger.error(f"Timeout error: {str(e)}")
        return JSONResponse(
            status_code=504,
            content={
                "error": "サーバーからの応答がタイムアウトしました。後ほど再度お試しください。"
            }
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "入力データが不正です。"
            }
        )
    except Exception as e:
        logger.error(f"予期せぬエラー: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "画像の解析中に問題が発生しました。後ほど再度お試しください。"
            }
        ) 