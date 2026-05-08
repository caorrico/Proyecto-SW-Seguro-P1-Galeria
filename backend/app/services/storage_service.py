import io
from datetime import timedelta
# pyrefly: ignore [missing-import]
from minio import Minio
# pyrefly: ignore [missing-import]
from minio.error import S3Error
from app.config import settings

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.minio_url,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=False  # Set to True if using HTTPS
        )
        self.bucket_name = settings.minio_bucket_name
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            print(f"Error ensuring bucket exists: {e}")

    def upload_file(self, file_data: bytes, file_name: str, content_type: str):
        try:
            self.client.put_object(
                self.bucket_name,
                file_name,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            return file_name
        except S3Error as e:
            print(f"Error uploading file to MinIO: {e}")
            return None

    def get_presigned_url(self, file_name: str, expires_minutes: int = 60):
        try:
            return self.client.get_presigned_url(
                "GET",
                self.bucket_name,
                file_name,
                expires=timedelta(minutes=expires_minutes)
            )
        except S3Error as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def delete_file(self, file_name: str):
        try:
            self.client.remove_object(self.bucket_name, file_name)
            return True
        except S3Error as e:
            print(f"Error deleting file from MinIO: {e}")
            return False

storage_service = StorageService()
