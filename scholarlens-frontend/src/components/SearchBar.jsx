import React, { useState } from 'react';
import { 
  TextField, Button, Box, FormControl, FormLabel, 
  RadioGroup, FormControlLabel, Radio, Paper 
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState('semantic');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query, searchType);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search for research papers... (e.g., 'transformer neural networks')"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
          sx={{ mb: 2 }}
          autoFocus
        />
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <FormControl component="fieldset">
            <FormLabel component="legend">Search Type</FormLabel>
            <RadioGroup
              row
              value={searchType}
              onChange={(e) => setSearchType(e.target.value)}
            >
              <FormControlLabel 
                value="semantic" 
                control={<Radio />} 
                label="Semantic (AI)" 
                disabled={loading}
              />
              <FormControlLabel 
                value="keyword" 
                control={<Radio />} 
                label="Keyword" 
                disabled={loading}
              />
            </RadioGroup>
          </FormControl>

          <Box sx={{ flexGrow: 1 }} />

          <Button
            type="submit"
            variant="contained"
            size="large"
            startIcon={<SearchIcon />}
            disabled={loading || !query.trim()}
          >
            {loading ? 'Searching...' : 'Search'}
          </Button>
        </Box>
      </Box>
    </Paper>
  );
}

export default SearchBar;