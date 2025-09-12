from __future__ import annotations

from io import BytesIO
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class S3FileMeta(BaseModel):
    size_bytes: int
    content_type: str
    last_modified: str
    etag: str = ""


class S3GetFilesResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_streams: Dict[str, BytesIO]
    file_metadata: Dict[str, S3FileMeta]
    failed_files: Optional[List[dict]] = None
    total_successful: int
    total_failed: int
