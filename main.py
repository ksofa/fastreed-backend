from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import ebooklib
from ebooklib import epub
from docx import Document
import os
import tempfile
from typing import Optional

app = FastAPI(title="FastReed API")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замените на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Максимальный размер файла (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def extract_text_from_epub(file_path: str) -> str:
    book = epub.read_epub(file_path)
    text = ""
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            text += item.get_content().decode('utf-8')
    return text

def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

@app.get("/")
async def root():
    return {"status": "ok", "message": "FastReed API is running"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой")
    
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # Извлекаем текст в зависимости от типа файла
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension == '.pdf':
            text = extract_text_from_pdf(temp_file_path)
        elif file_extension == '.epub':
            text = extract_text_from_epub(temp_file_path)
        elif file_extension == '.docx':
            text = extract_text_from_docx(temp_file_path)
        elif file_extension == '.txt':
            text = extract_text_from_txt(temp_file_path)
        else:
            raise HTTPException(status_code=400, detail="Неподдерживаемый формат файла")
        
        return JSONResponse(content={"text": text})
    
    finally:
        # Удаляем временный файл
        os.unlink(temp_file_path)

@app.post("/bionic")
async def bionic_text(text: str):
    # Простая реализация бионического чтения
    words = text.split()
    bionic_words = []
    for word in words:
        if len(word) > 3:
            bold_part = word[:len(word)//2]
            rest = word[len(word)//2:]
            bionic_words.append(f"<b>{bold_part}</b>{rest}")
        else:
            bionic_words.append(word)
    
    return {"bionic_text": " ".join(bionic_words)}

@app.post("/rsvp")
async def prepare_rsvp(text: str, speed: Optional[int] = 300):
    # Подготовка слов для RSVP чтения
    words = text.split()
    return {
        "words": words,
        "speed": speed
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 