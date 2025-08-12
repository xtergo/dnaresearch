import axios from 'axios';

const API_BASE_URL = 'http://localhost:7777';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.message || 'Server error occurred';
      throw new Error(message);
    } else if (error.request) {
      // Request was made but no response received
      throw new Error('Unable to connect to server. Please check your connection.');
    } else {
      // Something else happened
      throw new Error('An unexpected error occurred');
    }
  }
);

export const geneService = {
  searchGenes: async (query, limit = 10) => {
    const response = await api.get('/genes/search', {
      params: { query, limit }
    });
    return response.data;
  },

  getGeneDetails: async (symbol) => {
    const response = await api.get(`/genes/${symbol}`);
    return response.data;
  },

  interpretVariant: async (gene, variant, vcfData = null) => {
    const response = await api.post(`/genes/${gene}/interpret`, {
      variant,
      vcf_data: vcfData
    });
    return response.data;
  },

  getGeneSummary: async (gene) => {
    const response = await api.get(`/genes/${gene}/summary`);
    return response.data;
  }
};

export const theoryService = {
  listTheories: async (filters = {}) => {
    const response = await api.get('/theories', {
      params: filters
    });
    return response.data;
  },

  getTheoryDetails: async (theoryId, version = null) => {
    const params = version ? { version } : {};
    const response = await api.get(`/theories/${theoryId}`, {
      params
    });
    return response.data;
  },

  createTheory: async (theoryData) => {
    // Handle both direct theory data and wrapped format
    const payload = theoryData.theory_data ? theoryData : { theory_data: theoryData, author: theoryData.author || 'anonymous' };
    const response = await api.post('/theories', payload);
    return response.data;
  },

  updateTheory: async (theoryId, version, updates, author = 'anonymous') => {
    const response = await api.put(`/theories/${theoryId}`, {
      version,
      updates,
      author
    });
    return response.data;
  },

  deleteTheory: async (theoryId, version) => {
    const response = await api.delete(`/theories/${theoryId}`, {
      params: { version }
    });
    return response.data;
  },

  getTheoryTemplate: async (scope = 'autism') => {
    const response = await api.get(`/theories/templates/${scope}`);
    return response.data;
  },

  validateTheory: async (theoryData) => {
    const response = await api.post('/theories/validate', theoryData);
    return response.data;
  },

  executeTheory: async (theoryId, theory, vcfData, familyId = 'default') => {
    const response = await api.post(`/theories/${theoryId}/execute`, {
      theory,
      vcf_data: vcfData,
      family_id: familyId
    });
    return response.data;
  },

  addEvidence: async (theoryId, theoryVersion, familyId, bayesFactor, evidenceType = 'execution', weight = 1.0, source = 'manual_entry') => {
    const response = await api.post(`/theories/${theoryId}/evidence`, {
      theory_version: theoryVersion,
      family_id: familyId,
      bayes_factor: bayesFactor,
      evidence_type: evidenceType,
      weight,
      source
    });
    return response.data;
  },

  getEvidence: async (theoryId, theoryVersion) => {
    const response = await api.get(`/theories/${theoryId}/evidence`, {
      params: { theory_version: theoryVersion }
    });
    return response.data;
  },

  getPosterior: async (theoryId, theoryVersion, prior = 0.1) => {
    const response = await api.get(`/theories/${theoryId}/posterior`, {
      params: { theory_version: theoryVersion, prior }
    });
    return response.data;
  },

  getEvidenceStats: async (theoryId, theoryVersion) => {
    const response = await api.get(`/theories/${theoryId}/evidence/stats`, {
      params: { theory_version: theoryVersion }
    });
    return response.data;
  }
};

export const fileService = {
  createPresignedUpload: async (filename, fileSize, fileType, checksum, userId = 'anonymous') => {
    const response = await api.post('/files/presign', {
      filename,
      file_size: fileSize,
      file_type: fileType,
      checksum,
      user_id: userId
    });
    return response.data;
  },

  getUploadStatus: async (uploadId) => {
    const response = await api.get(`/files/uploads/${uploadId}`);
    return response.data;
  },

  completeUpload: async (uploadId, actualChecksum) => {
    const response = await api.post(`/files/uploads/${uploadId}/complete`, {
      actual_checksum: actualChecksum
    });
    return response.data;
  },

  listUploads: async (userId = null, status = null) => {
    const params = {};
    if (userId) params.user_id = userId;
    if (status) params.status = status;
    
    const response = await api.get('/files/uploads', { params });
    return response.data;
  }
};

export default api;