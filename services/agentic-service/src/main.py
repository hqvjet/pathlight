from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import openai
from dotenv import load_dotenv
import os
from mangum import Mangum
from boto3 import client

from file_route import extract_content_with_tags  # Assuming this function is defined in file_route.py
from split_text import split_into_chunks  # Assuming this function is defined in split_text.py


# Create FastAPI instance
app = FastAPI()

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure CORS
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize S3 client
s3_client = client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
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

@app.post("/upload-to-s3")
def upload_to_s3(files: List[UploadFile] = File(...)):
    bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
    if not bucket_name:
        raise HTTPException(status_code=500, detail="S3 bucket name not configured.")

    uploaded_files = []

    for file in files:
        try:
            s3_client.upload_fileobj(
                file.file,
                bucket_name,
                file.filename
            )
            uploaded_files.append(file.filename)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload {file.filename}: {str(e)}")

    return {"uploaded_files": uploaded_files}

handler = Mangum(app)                                                                                                                                                       yghtt