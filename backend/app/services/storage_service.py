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
            secure=False
        )
        self.buckets = {
            "quarantine": settings.minio_bucket_quarantine,
            "public": settings.minio_bucket_public,
            "evidence": settings.minio_bucket_evidence
        }
        self._ensure_buckets_exist()

    def _ensure_buckets_exist(self):
        for name, bucket in self.buckets.items():
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    print(f"Created bucket: {bucket}")
            except S3Error as e:
                print(f"Error ensuring bucket {bucket} exists: {e}")

    def upload_to_quarantine(self, file_data: bytes, file_name: str, content_type: str):
        try:
            self.client.put_object(
                self.buckets["quarantine"],
                file_name,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            return file_name
        except S3Error as e:
            print(f"Error uploading to quarantine: {e}")
            return None

    def move_object(self, source_bucket_key: str, dest_bucket_key: str, file_name: str):
        """Mueve un objeto entre buckets (Copy + Delete). Con fallback para migración."""
        try:
            dst = self.buckets[dest_bucket_key]
            
            # Lista de buckets donde podría estar el archivo (orden de probabilidad)
            potential_sources = [self.buckets[source_bucket_key], "secureframe-gallery", "uploads-quarantine", "gallery-public"]
            
            actual_source = None
            for bucket in potential_sources:
                try:
                    self.client.stat_object(bucket, file_name)
                    actual_source = bucket
                    break
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).debug(f"Stat object check failed in bucket {bucket}: {e}")
                    continue
            
            if not actual_source:
                print(f"CRITICAL: File {file_name} not found in any bucket.")
                return False

            # Copy
            from minio.commonconfig import CopySource
            self.client.copy_object(
                dst,
                file_name,
                CopySource(actual_source, file_name)
            )
            # Delete original
            self.client.remove_object(actual_source, file_name)
            return True
        except Exception as e:
            print(f"Error moving object: {e}")
            return False

    def get_presigned_url(self, bucket_key: str, file_name: str, expires_minutes: int = 5):
        try:
            return self.client.get_presigned_url(
                "GET",
                self.buckets[bucket_key],
                file_name,
                expires=timedelta(minutes=expires_minutes)
            )
        except S3Error as e:
            print(f"Error generating presigned URL for {bucket_key}: {e}")
            return None

    def delete_file(self, bucket_key: str, file_name: str):
        try:
            self.client.remove_object(self.buckets[bucket_key], file_name)
            return True
        except S3Error as e:
            print(f"Error deleting file from {bucket_key}: {e}")
            return False

storage_service = StorageService()
