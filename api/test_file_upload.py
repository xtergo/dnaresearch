"""Tests for secure file upload functionality"""

import pytest
from fastapi.testclient import TestClient
from file_upload_manager import FileType, FileUploadManager, UploadStatus
from main import app

client = TestClient(app)


class TestFileUploadManager:
    """Test the FileUploadManager class"""

    def setup_method(self):
        self.manager = FileUploadManager()

    def test_create_presigned_upload_vcf(self):
        """Test creating pre-signed upload for VCF file"""
        upload = self.manager.create_presigned_upload(
            filename="sample.vcf.gz",
            file_size=1024000,
            file_type="vcf",
            checksum="abc123",
            user_id="test_user",
        )

        assert upload.filename == "sample.vcf.gz"
        assert upload.file_type == FileType.VCF
        assert upload.file_size == 1024000
        assert upload.status == UploadStatus.PENDING
        assert upload.user_id == "test_user"
        assert "s3.amazonaws.com" in upload.presigned_url

    def test_create_presigned_upload_fastq(self):
        """Test creating pre-signed upload for FASTQ file"""
        upload = self.manager.create_presigned_upload(
            filename="reads.fastq.gz",
            file_size=5000000000,  # 5GB
            file_type="fastq",
            checksum="def456",
        )

        assert upload.file_type == FileType.FASTQ
        assert upload.status == UploadStatus.PENDING

    def test_invalid_file_type(self):
        """Test invalid file type rejection"""
        with pytest.raises(ValueError, match="Unsupported file type"):
            self.manager.create_presigned_upload(
                filename="test.txt",
                file_size=1000,
                file_type="invalid",
                checksum="abc123",
            )

    def test_invalid_file_extension(self):
        """Test invalid file extension rejection"""
        with pytest.raises(ValueError, match="Invalid file extension"):
            self.manager.create_presigned_upload(
                filename="test.txt", file_size=1000, file_type="vcf", checksum="abc123"
            )

    def test_file_too_large(self):
        """Test file size limit enforcement"""
        with pytest.raises(ValueError, match="File too large"):
            self.manager.create_presigned_upload(
                filename="huge.vcf",
                file_size=200 * 1024 * 1024,  # 200MB (over 100MB limit)
                file_type="vcf",
                checksum="abc123",
            )

    def test_validate_upload_completion_success(self):
        """Test successful upload validation"""
        upload = self.manager.create_presigned_upload(
            filename="test.vcf",
            file_size=1000,
            file_type="vcf",
            checksum="correct_checksum",
        )

        result = self.manager.validate_upload_completion(
            upload.upload_id, "correct_checksum"
        )

        assert result is True
        assert upload.status == UploadStatus.COMPLETED

    def test_validate_upload_completion_wrong_checksum(self):
        """Test upload validation with wrong checksum"""
        upload = self.manager.create_presigned_upload(
            filename="test.vcf",
            file_size=1000,
            file_type="vcf",
            checksum="correct_checksum",
        )

        result = self.manager.validate_upload_completion(
            upload.upload_id, "wrong_checksum"
        )

        assert result is False
        assert upload.status == UploadStatus.FAILED

    def test_get_upload_status(self):
        """Test getting upload status"""
        upload = self.manager.create_presigned_upload(
            filename="test.vcf", file_size=1000, file_type="vcf", checksum="abc123"
        )

        retrieved = self.manager.get_upload_status(upload.upload_id)
        assert retrieved == upload

        # Test non-existent upload
        assert self.manager.get_upload_status("nonexistent") is None

    def test_list_user_uploads(self):
        """Test listing user uploads"""
        # Create uploads for different users
        self.manager.create_presigned_upload(
            filename="file1.vcf",
            file_size=1000,
            file_type="vcf",
            checksum="abc1",
            user_id="user1",
        )
        self.manager.create_presigned_upload(
            filename="file2.vcf",
            file_size=1000,
            file_type="vcf",
            checksum="abc2",
            user_id="user1",
        )
        self.manager.create_presigned_upload(
            filename="file3.vcf",
            file_size=1000,
            file_type="vcf",
            checksum="abc3",
            user_id="user2",
        )

        # Test listing for user1
        user1_uploads = self.manager.list_user_uploads("user1")
        assert len(user1_uploads) == 2
        assert all(u.user_id == "user1" for u in user1_uploads)

        # Test listing for user2
        user2_uploads = self.manager.list_user_uploads("user2")
        assert len(user2_uploads) == 1
        assert user2_uploads[0].user_id == "user2"

    def test_get_upload_stats(self):
        """Test upload statistics"""
        # Create various uploads
        self.manager.create_presigned_upload(
            filename="file1.vcf", file_size=1000, file_type="vcf", checksum="abc1"
        )
        upload2 = self.manager.create_presigned_upload(
            filename="file2.fastq", file_size=2000, file_type="fastq", checksum="abc2"
        )

        # Complete one upload
        self.manager.validate_upload_completion(upload2.upload_id, "abc2")

        stats = self.manager.get_upload_stats()

        assert stats["total_uploads"] == 2
        assert stats["by_status"]["pending"] == 1
        assert stats["by_status"]["completed"] == 1
        assert stats["by_file_type"]["vcf"] == 1
        assert stats["by_file_type"]["fastq"] == 1
        assert stats["total_size_bytes"] == 2000  # Only completed uploads


class TestFileUploadAPI:
    """Test the file upload API endpoints"""

    def setup_method(self):
        """Reset upload manager for each test"""
        from main import file_upload_manager

        file_upload_manager.uploads.clear()

    def test_create_presigned_upload_endpoint(self):
        """Test creating pre-signed upload via API"""
        response = client.post(
            "/files/presign",
            json={
                "filename": "sample.vcf.gz",
                "file_size": 1024000,
                "file_type": "vcf",
                "checksum": "abc123def456",
                "user_id": "test_user",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "upload_id" in data
        assert "presigned_url" in data
        assert "expires_at" in data
        assert data["status"] == "pending"
        assert "s3.amazonaws.com" in data["presigned_url"]

    def test_create_presigned_upload_invalid_type(self):
        """Test API with invalid file type"""
        response = client.post(
            "/files/presign",
            json={
                "filename": "test.txt",
                "file_size": 1000,
                "file_type": "invalid",
                "checksum": "abc123",
            },
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_create_presigned_upload_file_too_large(self):
        """Test API with file too large"""
        response = client.post(
            "/files/presign",
            json={
                "filename": "huge.vcf",
                "file_size": 200 * 1024 * 1024,  # 200MB
                "file_type": "vcf",
                "checksum": "abc123",
            },
        )

        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]

    def test_get_upload_status_endpoint(self):
        """Test getting upload status via API"""
        # First create an upload
        create_response = client.post(
            "/files/presign",
            json={
                "filename": "test.vcf",
                "file_size": 1000,
                "file_type": "vcf",
                "checksum": "abc123",
            },
        )
        upload_id = create_response.json()["upload_id"]

        # Get status
        response = client.get(f"/files/uploads/{upload_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["upload_id"] == upload_id
        assert data["filename"] == "test.vcf"
        assert data["file_type"] == "vcf"
        assert data["status"] == "pending"

    def test_get_upload_status_not_found(self):
        """Test getting status for non-existent upload"""
        response = client.get("/files/uploads/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_complete_upload_endpoint(self):
        """Test completing upload via API"""
        # Create upload
        create_response = client.post(
            "/files/presign",
            json={
                "filename": "test.vcf",
                "file_size": 1000,
                "file_type": "vcf",
                "checksum": "correct_checksum",
            },
        )
        upload_id = create_response.json()["upload_id"]

        # Complete upload
        response = client.post(
            f"/files/uploads/{upload_id}/complete",
            json={"actual_checksum": "correct_checksum"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert data["validated"] is True
        assert data["upload_id"] == upload_id

    def test_complete_upload_wrong_checksum(self):
        """Test completing upload with wrong checksum"""
        # Create upload
        create_response = client.post(
            "/files/presign",
            json={
                "filename": "test.vcf",
                "file_size": 1000,
                "file_type": "vcf",
                "checksum": "correct_checksum",
            },
        )
        upload_id = create_response.json()["upload_id"]

        # Complete with wrong checksum
        response = client.post(
            f"/files/uploads/{upload_id}/complete",
            json={"actual_checksum": "wrong_checksum"},
        )

        assert response.status_code == 400
        assert "Checksum validation failed" in response.json()["detail"]

    def test_list_uploads_endpoint(self):
        """Test listing uploads via API"""
        # Create some uploads
        client.post(
            "/files/presign",
            json={
                "filename": "file1.vcf",
                "file_size": 1000,
                "file_type": "vcf",
                "checksum": "abc1",
                "user_id": "test_user",
            },
        )
        client.post(
            "/files/presign",
            json={
                "filename": "file2.fastq",
                "file_size": 2000,
                "file_type": "fastq",
                "checksum": "abc2",
                "user_id": "test_user",
            },
        )

        # List uploads
        response = client.get("/files/uploads?user_id=test_user")

        assert response.status_code == 200
        data = response.json()

        assert data["count"] == 2
        assert len(data["uploads"]) == 2
        assert all(u["status"] == "pending" for u in data["uploads"])

    def test_list_uploads_with_status_filter(self):
        """Test listing uploads with status filter"""
        response = client.get("/files/uploads?user_id=test_user&status=pending")

        assert response.status_code == 200
        data = response.json()

        assert all(u["status"] == "pending" for u in data["uploads"])

    def test_get_upload_stats_endpoint(self):
        """Test getting upload statistics via API"""
        response = client.get("/files/stats")

        assert response.status_code == 200
        data = response.json()

        assert "total_uploads" in data
        assert "by_status" in data
        assert "by_file_type" in data
        assert "total_size_mb" in data

    def test_cleanup_expired_uploads_endpoint(self):
        """Test cleanup endpoint"""
        response = client.post("/files/cleanup")

        assert response.status_code == 200
        data = response.json()

        assert "cleaned_up" in data
        assert "timestamp" in data
        assert isinstance(data["cleaned_up"], int)


class TestFileUploadSecurity:
    """Test security aspects of file upload"""

    def setup_method(self):
        self.manager = FileUploadManager()

    def test_presigned_url_contains_signature(self):
        """Test that pre-signed URLs contain security signature"""
        upload = self.manager.create_presigned_upload(
            filename="test.vcf", file_size=1000, file_type="vcf", checksum="abc123"
        )

        assert "signature=" in upload.presigned_url
        assert "expires=" in upload.presigned_url

    def test_upload_id_uniqueness(self):
        """Test that upload IDs are unique"""
        upload1 = self.manager.create_presigned_upload(
            filename="test.vcf", file_size=1000, file_type="vcf", checksum="abc1"
        )
        upload2 = self.manager.create_presigned_upload(
            filename="test.vcf", file_size=1000, file_type="vcf", checksum="abc2"
        )

        assert upload1.upload_id != upload2.upload_id

    def test_checksum_validation_prevents_tampering(self):
        """Test that checksum validation prevents file tampering"""
        upload = self.manager.create_presigned_upload(
            filename="test.vcf",
            file_size=1000,
            file_type="vcf",
            checksum="original_checksum",
        )

        # Attempt to complete with different checksum (simulating tampering)
        result = self.manager.validate_upload_completion(
            upload.upload_id, "tampered_checksum"
        )

        assert result is False
        assert upload.status == UploadStatus.FAILED


class TestFileUploadEdgeCases:
    """Test edge cases and error handling"""

    def test_missing_required_fields_api(self):
        """Test API with missing required fields"""
        response = client.post(
            "/files/presign",
            json={
                "filename": "test.vcf",
                # Missing file_size, file_type, checksum
            },
        )

        assert response.status_code == 422  # Validation error

    def test_invalid_status_filter(self):
        """Test listing with invalid status filter"""
        response = client.get("/files/uploads?status=invalid_status")

        assert response.status_code == 400
        assert "Invalid status" in response.json()["detail"]

    def test_complete_nonexistent_upload(self):
        """Test completing non-existent upload"""
        response = client.post(
            "/files/uploads/nonexistent/complete", json={"actual_checksum": "abc123"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
