import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link } from 'react-router-dom';
import SearchIcon from '@mui/icons-material/Search';
import HomeIcon from '@mui/icons-material/Home';

function Navbar() {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography 
          variant="h6" 
          component="div" 
          sx={{ flexGrow: 1, display: 'flex', alignItems: 'center' }}
        >
          🔬 ScholarLens
        </Typography>
        
        <Box>
          <Button 
            color="inherit" 
            component={Link} 
            to="/" 
            startIcon={<HomeIcon />}
          >
            Home
          </Button>
          <Button 
            color="inherit" 
            component={Link} 
            to="/search" 
            startIcon={<SearchIcon />}
          >
            Search
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default Navbar;