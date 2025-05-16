from fastapi import APIRouter, File, UploadFile, HTTPException
from backend.app.services.ocr_service import extract_text_from_image
from backend.app.services.data_structuring_service import extract_key_data

router = APIRouter()

@router.post("/upload-ocr", summary="Upload de imagem com OCR e extração de dados")
async def upload_ocr(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo não é imagem")
    try:
        contents = await file.read()
        ocr_results = extract_text_from_image(contents)
        structured_data = extract_key_data(ocr_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no OCR: {str(e)}")
    return {
        "filename": file.filename,
        "ocr_results": ocr_results,
        "structured_data": structured_data
    }