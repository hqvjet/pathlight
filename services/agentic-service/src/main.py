from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import openai
from dotenv import load_dotenv
import os
from mangum import Mangum

from file_route import extract_content_with_tags  # Assuming this function is defined in file_route.py
from split_text import split_into_chunks  # Assuming this function is defined in split_text.py


# Create FastAPI instance
app = FastAPI()

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://example.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a basic route
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}

@app.post("/vectorize")
def upload_files(files: List[UploadFile] = File(...)):
    allowed_extensions = {"docx", "pdf", "pptx"}
    file_contents = {}


@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration (without sensitive data)"""
    return {
        "IS_LAMBDA": config.IS_LAMBDA,
        "MAX_TOKENS_PER_CHUNK": config.MAX_TOKENS_PER_CHUNK,
        "MAX_FILE_SIZE_MB": config.MAX_FILE_SIZE_MB,
        "ALLOWED_FILE_EXTENSIONS": list(config.ALLOWED_FILE_EXTENSIONS),
        "OPENAI_API_KEY_SET": bool(config.OPENAI_API_KEY),
        "LOG_LEVEL": config.LOG_LEVEL,
    }

        structured_content = extract_content_with_tags(file, extension)
        file_contents[file.filename] = structured_content

    chunks = []
    for filename, content in file_contents.items():
        chunks.extend(split_into_chunks(content, source_info=filename))

    embeddings = []
    for chunk in chunks:
        response = openai.Embedding.create(
            input=chunk["chunk_text"],
            model="text-embedding-3-small"
        )
        embeddings.append({
            "chunk_id": chunk["chunk_id"],
            "embedding": response["data"][0]["embedding"],
            "chunk_text": chunk["chunk_text"],
            "source_info": chunk["source_info"]
        })

    return {"embeddings": embeddings}

handler = Mangum(app)