import io
import os
import struct
import uuid
from pathlib import Path

from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import numpy as np

from app.config import settings

# MIME magic numbers para validación real (no confiar en extensión)
_MAGIC_BYTES: dict[bytes, str] = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"RIFF": "image/webp",   # RIFF....WEBP — validación adicional más abajo
    b"BM": "image/bmp",
}
_ALLOWED_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"}


def detect_mime_type(data: bytes) -> str | None:
    """Detecta el tipo MIME real leyendo los magic bytes del archivo."""
    for magic, mime in _MAGIC_BYTES.items():
        if data[:len(magic)] == magic:
            if mime == "image/webp":
                # Verificar que sea realmente WEBP: bytes 8-11 == b'WEBP'
                return "image/webp" if data[8:12] == b"WEBP" else None
            return mime
    return None


def validate_and_process_image(
    file_bytes: bytes,
    original_filename: str,
) -> tuple[bytes, str, str]:
    """
    Valida el archivo, elimina EXIF y re-encodea.
    Retorna (processed_bytes, mime_type, stored_extension).
    Lanza ValueError si no es una imagen válida.
    """
    # 1. Validar tipo real por magic bytes
    mime = detect_mime_type(file_bytes)
    if mime not in _ALLOWED_MIMES:
        raise ValueError(f"File type not allowed. Detected: {mime or 'unknown'}")

    # 2. Abrir con Pillow para validación estructural
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()  # verifica integridad sin decodificar completamente
    except Exception:
        raise ValueError("File is not a valid image or is corrupted")

    # 3. Re-abrir (verify cierra el stream) + strip EXIF + re-encode
    img = Image.open(io.BytesIO(file_bytes))

    # Convertir a RGB para eliminar canales EXIF y metadata embebida
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    # 4. Guardar sin metadata EXIF (Pillow no copia EXIF en el save por defecto)
    output = io.BytesIO()
    save_format = "JPEG"
    extension  = ".jpg"

    if mime == "image/png":
        # Mantener PNG para imágenes con transparencia
        save_format = "PNG"
        extension   = ".png"
        if img.mode == "RGB":
            pass  # OK
    elif mime == "image/gif":
        save_format = "GIF"
        extension   = ".gif"
    elif mime == "image/webp":
        save_format = "WEBP"
        extension   = ".webp"

    img.save(output, format=save_format, quality=90 if save_format == "JPEG" else None)
    processed = output.getvalue()

    return processed, mime, extension


def generate_stored_filename(extension: str) -> str:
    """Genera nombre único seguro (UUID4) para almacenar el archivo."""
    return f"{uuid.uuid4().hex}{extension}"


def save_file(data: bytes, stored_filename: str) -> str:
    """Guarda el archivo en el directorio de uploads. Retorna la ruta completa."""
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / stored_filename
    file_path.write_bytes(data)
    return str(file_path)


def check_eof_markers(file_bytes: bytes, mime: str) -> bool:
    """
    Detecta datos ocultos tras el marcador EOF del formato.
    - JPEG: datos tras el marcador FFD9
    - PNG: datos tras el chunk IEND
    """
    try:
        if "jpeg" in mime:
            eof_marker = b"\xff\xd9"
            idx = file_bytes.rfind(eof_marker)
            if idx != -1 and idx + 2 < len(file_bytes):
                trailing = file_bytes[idx + 2:].strip(b"\x00")
                return len(trailing) > 16  # tolerancia para padding
        elif "png" in mime:
            iend = b"IEND\xae\x42\x60\x82"
            idx = file_bytes.rfind(iend)
            if idx != -1 and idx + 8 < len(file_bytes):
                trailing = file_bytes[idx + 8:].strip(b"\x00")
                return len(trailing) > 4
    except Exception as e:
        import logging
        logging.getLogger(__name__).debug(f"EOF check error: {e}")
    return False
