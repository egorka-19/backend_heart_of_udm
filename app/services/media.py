import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


def ensure_upload_dir() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)


def public_url_for_relative(rel_path: str) -> str:
    base = settings.public_base_url.rstrip("/")
    p = rel_path.lstrip("/")
    return f"{base}/uploads/{p}"


async def save_upload_bytes(subdir: str, file: UploadFile, suffix: str = ".jpg") -> str:
    ensure_upload_dir()
    dest_dir = Path(settings.upload_dir) / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4()}{suffix}"
    dest = dest_dir / name
    content = await file.read()
    dest.write_bytes(content)
    rel = str(Path(subdir) / name).replace("\\", "/")
    return rel


def relative_to_abs_path(rel: str) -> Path:
    return Path(settings.upload_dir) / rel
