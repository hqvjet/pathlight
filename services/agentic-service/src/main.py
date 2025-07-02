from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from file_route import extract_content_with_tags  # Assuming this function is defined in file_route.py
from split_text import split_into_chunks  # Assuming this function is defined in split_text.py


# Create FastAPI instance
app = FastAPI()

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

    for file in files:
        extension = file.filename.split(".")[-1]
        if extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File type not allowed: {file.filename}")

        structured_content = extract_content_with_tags(file, extension)
        file_contents[file.filename] = structured_content

    chunks = []
    for filename, content in file_contents.items():
        chunks.extend(split_into_chunks(content, source_info=filename))

    return {"chunks": chunks}