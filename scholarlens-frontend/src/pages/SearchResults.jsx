import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Alert, Chip } from '@mui/material';
import { useLocation } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import PaperCard from '../components/PaperCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { searchPapersSemantic, searchPapersKeyword } from '../services/api';
import AccessTimeIcon from '@mui/icons-material/AccessTime';

function SearchResults() {
  const location = useLocation();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchInfo, setSearchInfo] = useState(null);

  useEffect(() => {
    if (location.state?.query) {
      handleSearch(location.state.query, location.state.searchType || 'semantic');
    }
  }, [location.state]);

  const handleSearch = async (query, searchType) => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Searching:', { query, searchType });
      
      let response;
      if (searchType === 'semantic') {
        response = await searchPapersSemantic(query, 20);
      } else {
        response = await searchPapersKeyword(query, 1, 20);
      }

      console.log('Search response:', response.data);
      
      setResults(response.data.results || []);
      setSearchInfo({
        query: query,
        type: searchType === 'semantic' ? 'Semantic Search' : 'Keyword Search',
        total: response.data.total || response.data.results?.length || 0,
        time: response.data.processing_time_ms
      });
    } catch (err) {
      console.error('Search error:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Search failed';
      setError(`Error: ${errorMsg}. Make sure backend is running on port 8000.`);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        Search Research Papers
      </Typography>
      
      <SearchBar onSearch={handleSearch} loading={loading} />

      {searchInfo && !loading && (
        <Alert 
          severity="info" 
          sx={{ mb: 3 }}
          icon={<AccessTimeIcon />}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <span>
              Found <strong>{searchInfo.total}</strong> result{searchInfo.total !== 1 ? 's' : ''} for 
              "<strong>{searchInfo.query}</strong>"
            </span>
            <Chip 
              label={searchInfo.type} 
              size="small" 
              color="primary"
              sx={{ ml: 1 }}
            />
            {searchInfo.time && (
              <Chip 
                label={`${searchInfo.time.toFixed(0)}ms`} 
                size="small" 
                variant="outlined"
              />
            )}
          </Box>
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && <LoadingSpinner message="Searching papers..." />}

      {!loading && results.length > 0 && (
        <Box>
          <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
            Search Results ({results.length})
          </Typography>
          {results.map((paper) => (
            <PaperCard key={paper.paper_id} paper={paper} />
          ))}
        </Box>
      )}

      {!loading && searchInfo && results.length === 0 && !error && (
        <Box 
          sx={{ 
            textAlign: 'center', 
            mt: 6, 
            p: 4,
            bgcolor: 'background.paper',
            borderRadius: 2,
            border: '1px dashed',
            borderColor: 'divider'
          }}
        >
          <Typography variant="h5" gutterBottom color="text.secondary">
            No papers found
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            No results for "<strong>{searchInfo.query}</strong>"
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try different keywords or switch search type
          </Typography>
        </Box>
      )}

      {!loading && !searchInfo && (
        <Box sx={{ textAlign: 'center', mt: 6, p: 4 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Enter a search query above to find research papers
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try: "neural networks", "machine learning", or "transformers"
          </Typography>
        </Box>
      )}
    </Container>
  );
}

export default SearchResults;