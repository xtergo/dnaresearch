import React, { useState, useEffect } from 'react';
import { fileService } from '../services/api';

const FileUpload = () => {
  const [uploads, setUploads] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    loadUploads();
  }, []);

  const loadUploads = async () => {
    try {
      const data = await fileService.listUploads();
      setUploads(data.uploads || []);
    } catch (err) {
      setError('Failed to load upload history.');
    }
  };

  const calculateChecksum = async (file) => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const buffer = e.target.result;
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        resolve(hashHex);
      };
      reader.readAsArrayBuffer(file);
    });
  };

  const handleFileUpload = async (files) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      for (const file of files) {
        // Validate file type
        const validTypes = ['.vcf', '.fastq', '.fq', '.bam', '.cram', '.gz'];
        const isValidType = validTypes.some(type => 
          file.name.toLowerCase().endsWith(type) || 
          file.name.toLowerCase().includes(type)
        );

        if (!isValidType) {
          throw new Error(`Invalid file type: ${file.name}. Supported types: VCF, FASTQ, BAM, CRAM`);
        }

        // Calculate checksum
        const checksum = await calculateChecksum(file);

        // Create presigned upload
        const uploadData = await fileService.createPresignedUpload(
          file.name,
          file.size,
          getFileType(file.name),
          checksum
        );

        // Upload file to presigned URL
        const uploadResponse = await fetch(uploadData.presigned_url, {
          method: 'PUT',
          body: file,
          headers: {
            'Content-Type': file.type || 'application/octet-stream'
          }
        });

        if (!uploadResponse.ok) {
          throw new Error(`Upload failed for ${file.name}`);
        }

        // Complete upload
        await fileService.completeUpload(uploadData.upload_id, checksum);
      }

      setSuccess(`Successfully uploaded ${files.length} file(s)`);
      await loadUploads();
    } catch (err) {
      setError(err.message || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const getFileType = (filename) => {
    const name = filename.toLowerCase();
    if (name.includes('.vcf')) return 'vcf';
    if (name.includes('.fastq') || name.includes('.fq')) return 'fastq';
    if (name.includes('.bam')) return 'bam';
    if (name.includes('.cram')) return 'cram';
    return 'other';
  };

  const getFileTypeColor = (fileType) => {
    const colors = {
      vcf: '#007bff',
      fastq: '#28a745',
      bam: '#ffc107',
      cram: '#dc3545',
      other: '#6c757d'
    };
    return colors[fileType] || '#6c757d';
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: '#ffc107',
      uploading: '#007bff',
      completed: '#28a745',
      failed: '#dc3545',
      expired: '#6c757d'
    };
    return colors[status] || '#6c757d';
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(Array.from(e.target.files));
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <h2>Genomic File Upload</h2>
      
      {/* Upload Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        style={{
          border: dragActive ? '2px dashed #007bff' : '2px dashed #ddd',
          borderRadius: '8px',
          padding: '40px',
          textAlign: 'center',
          backgroundColor: dragActive ? '#f0f8ff' : '#f8f9fa',
          marginBottom: '20px',
          cursor: 'pointer',
          transition: 'all 0.3s ease'
        }}
      >
        <input
          type="file"
          multiple
          accept=".vcf,.fastq,.fq,.bam,.cram,.gz"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          id="file-upload"
          disabled={uploading}
        />
        
        <div style={{ fontSize: '48px', marginBottom: '10px', color: '#007bff' }}>
          📁
        </div>
        
        <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>
          {dragActive ? 'Drop files here' : 'Upload Genomic Files'}
        </h3>
        
        <p style={{ margin: '0 0 20px 0', color: '#666' }}>
          Drag and drop files here, or{' '}
          <label
            htmlFor="file-upload"
            style={{ color: '#007bff', cursor: 'pointer', textDecoration: 'underline' }}
          >
            click to browse
          </label>
        </p>
        
        <div style={{ fontSize: '14px', color: '#888' }}>
          Supported formats: VCF, FASTQ, BAM, CRAM (including .gz compressed)
        </div>
        
        {uploading && (
          <div style={{ marginTop: '20px' }}>
            <div style={{ color: '#007bff', fontWeight: 'bold' }}>
              Uploading files...
            </div>
            <div style={{
              width: '100%',
              height: '4px',
              backgroundColor: '#e9ecef',
              borderRadius: '2px',
              marginTop: '10px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: '100%',
                height: '100%',
                backgroundColor: '#007bff',
                animation: 'progress 2s infinite'
              }} />
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      {error && (
        <div style={{
          padding: '15px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{
          padding: '15px',
          backgroundColor: '#d4edda',
          color: '#155724',
          border: '1px solid #c3e6cb',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          {success}
        </div>
      )}

      {/* Upload History */}
      <div>
        <h3>Upload History ({uploads.length})</h3>
        {uploads.length === 0 ? (
          <div style={{
            padding: '40px',
            textAlign: 'center',
            color: '#666',
            border: '1px dashed #ddd',
            borderRadius: '4px'
          }}>
            No uploads yet. Upload your first genomic file above.
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '10px' }}>
            {uploads.map((upload) => (
              <div
                key={upload.upload_id}
                style={{
                  padding: '15px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  backgroundColor: '#fff'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '5px' }}>
                      {upload.filename}
                    </div>
                    <div style={{ display: 'flex', gap: '15px', alignItems: 'center', marginBottom: '8px' }}>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          color: 'white',
                          backgroundColor: getFileTypeColor(upload.file_type)
                        }}
                      >
                        {upload.file_type.toUpperCase()}
                      </span>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          color: 'white',
                          backgroundColor: getStatusColor(upload.status)
                        }}
                      >
                        {upload.status.toUpperCase()}
                      </span>
                      <span style={{ fontSize: '12px', color: '#666' }}>
                        {formatFileSize(upload.file_size)}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#888' }}>
                      Upload ID: {upload.upload_id}
                    </div>
                    <div style={{ fontSize: '12px', color: '#888' }}>
                      Created: {new Date(upload.created_at).toLocaleString()}
                    </div>
                    {upload.user_id && (
                      <div style={{ fontSize: '12px', color: '#888' }}>
                        User: {upload.user_id}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes progress {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  );
};

export default FileUpload;