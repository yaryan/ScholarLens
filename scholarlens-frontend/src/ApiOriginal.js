cat > src/services/api.js << 'EOF'
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export const healthCheck = () => api.get('/health/');

export const getSystemStatus = () => api.get('/health/status');

export const searchPapersSemantic = (query, topK = 10) => 
  api.post('/api/search/semantic', { 
    query: query, 
    top_k: topK 
  });

export const searchPapersKeyword = (query, page = 1, pageSize = 20) => 
  api.get('/api/search/papers', {
    params: { query, page, page_size: pageSize }
  });

export const listPapers = (page = 1, pageSize = 20) => 
  api.get('/api/papers/', { params: { page, page_size: pageSize } });

export const getPaperById = (paperId) => 
  api.get('/api/papers/${paperId}');

export default api;
