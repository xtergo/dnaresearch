"""Secure file upload manager with pre-signed URLs"""

import hashlib
import hmac
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class FileType(Enum):
    VCF = "vcf"
    FASTQ = "fastq"
    BAM = "bam"
    CRAM = "cram"


class UploadStatus(Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class FileUpload:
    upload_id: str
    filename: str
    file_type: FileType
    file_size: int
    checksum: str
    presigned_url: str
    expires_at: str
    status: UploadStatus
    created_at: str
    user_id: str = "anonymous"
    metadata: Dict[str, Any] = None


class FileUploadManager:
    """Manage secure file uploads with pre-signed URLs"""

    def __init__(self):
        self.uploads = {}  # In production: database
        self.secret_key = "secure_upload_secret_key_2025"
        self.base_url = "https://dnaresearch-uploads.s3.amazonaws.com"

        # File type validation
        self.allowed_extensions = {
            FileType.VCF: [".vcf", ".vcf.gz"],
            FileType.FASTQ: [".fastq", ".fastq.gz", ".fq", ".fq.gz"],
            FileType.BAM: [".bam"],
            FileType.CRAM: [".cram"],
        }

        # Size limits (bytes)
        self.max_file_sizes = {
            FileType.VCF: 100 * 1024 * 1024,  # 100MB
            FileType.FASTQ: 10 * 1024 * 1024 * 1024,  # 10GB
            FileType.BAM: 5 * 1024 * 1024 * 1024,  # 5GB
            FileType.CRAM: 2 * 1024 * 1024 * 1024,  # 2GB
        }

    def create_presigned_upload(
        self,
        filename: str,
        file_size: int,
        file_type: str,
        checksum: str,
        user_id: str = "anonymous",
        expires_in_hours: int = 24,
    ) -> FileUpload:
        """Create pre-signed URL for secure file upload"""

        # Validate file type
        try:
            file_type_enum = FileType(file_type.lower())
        except ValueError:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Validate file extension
        if not any(
            filename.lower().endswith(ext)
            for ext in self.allowed_extensions[file_type_enum]
        ):
            raise ValueError(f"Invalid file extension for {file_type}")

        # Validate file size
        if file_size > self.max_file_sizes[file_type_enum]:
            max_size_mb = self.max_file_sizes[file_type_enum] / (1024 * 1024)
            raise ValueError(
                f"File too large. Max size for {file_type}: {max_size_mb}MB"
            )

        # Generate upload ID
        upload_id = self._generate_upload_id(filename, user_id)

        # Generate pre-signed URL
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        presigned_url = self._generate_presigned_url(upload_id, filename, expires_at)

        # Create upload record
        upload = FileUpload(
            upload_id=upload_id,
            filename=filename,
            file_type=file_type_enum,
            file_size=file_size,
            checksum=checksum,
            presigned_url=presigned_url,
            expires_at=expires_at.isoformat() + "Z",
            status=UploadStatus.PENDING,
            created_at=datetime.utcnow().isoformat() + "Z",
            user_id=user_id,
            metadata={},
        )

        self.uploads[upload_id] = upload
        return upload

    def _generate_upload_id(self, filename: str, user_id: str) -> str:
        """Generate unique upload ID"""
        unique_id = str(uuid.uuid4())
        timestamp = str(int(time.time() * 1000000))  # microseconds for uniqueness
        data = f"{filename}_{user_id}_{timestamp}_{unique_id}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _generate_presigned_url(
        self, upload_id: str, filename: str, expires_at: datetime
    ) -> str:
        """Generate pre-signed URL (mock S3 implementation)"""
        # In production: use boto3 to generate real S3 pre-signed URL
        timestamp = int(expires_at.timestamp())

        # Create signature
        string_to_sign = f"PUT\n{upload_id}\n{filename}\n{timestamp}"
        signature = hmac.new(
            self.secret_key.encode(), string_to_sign.encode(), hashlib.sha256
        ).hexdigest()

        return f"{self.base_url}/{upload_id}/{filename}?expires={timestamp}&signature={signature}"

    def validate_upload_completion(self, upload_id: str, actual_checksum: str) -> bool:
        """Validate completed upload"""
        upload = self.uploads.get(upload_id)
        if not upload:
            return False

        # Check expiration
        expires_at = datetime.fromisoformat(upload.expires_at.replace("Z", ""))
        if datetime.utcnow() > expires_at:
            upload.status = UploadStatus.EXPIRED
            return False

        # Validate checksum
        if upload.checksum != actual_checksum:
            upload.status = UploadStatus.FAILED
            return False

        upload.status = UploadStatus.COMPLETED
        return True

    def get_upload_status(self, upload_id: str) -> Optional[FileUpload]:
        """Get upload status"""
        return self.uploads.get(upload_id)

    def update_upload_status(
        self, upload_id: str, status: UploadStatus, metadata: Dict[str, Any] = None
    ):
        """Update upload status"""
        upload = self.uploads.get(upload_id)
        if upload:
            upload.status = status
            if metadata:
                upload.metadata.update(metadata)

    def list_user_uploads(
        self, user_id: str, status: UploadStatus = None
    ) -> List[FileUpload]:
        """List uploads for a user"""
        uploads = [u for u in self.uploads.values() if u.user_id == user_id]
        if status:
            uploads = [u for u in uploads if u.status == status]
        return sorted(uploads, key=lambda x: x.created_at, reverse=True)

    def cleanup_expired_uploads(self) -> int:
        """Clean up expired uploads"""
        now = datetime.utcnow()
        expired_count = 0

        for upload_id, upload in list(self.uploads.items()):
            expires_at = datetime.fromisoformat(upload.expires_at.replace("Z", ""))
            if now > expires_at and upload.status == UploadStatus.PENDING:
                upload.status = UploadStatus.EXPIRED
                expired_count += 1

        return expired_count

    def get_upload_stats(self) -> Dict[str, Any]:
        """Get upload statistics"""
        total = len(self.uploads)
        by_status = {}
        by_type = {}
        total_size = 0

        for upload in self.uploads.values():
            # Count by status
            status = upload.status.value
            by_status[status] = by_status.get(status, 0) + 1

            # Count by type
            file_type = upload.file_type.value
            by_type[file_type] = by_type.get(file_type, 0) + 1

            # Total size
            if upload.status == UploadStatus.COMPLETED:
                total_size += upload.file_size

        return {
            "total_uploads": total,
            "by_status": by_status,
            "by_file_type": by_type,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
