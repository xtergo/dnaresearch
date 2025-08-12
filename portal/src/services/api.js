import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

export default api;