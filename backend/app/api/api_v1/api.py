from .endpoints import ocr_upload
api_router.include_router(ocr_upload.router, prefix="/ocr", tags=["OCR"])