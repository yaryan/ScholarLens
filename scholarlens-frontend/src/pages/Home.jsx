import React, { useEffect, useState } from 'react';
import { 
  Container, Typography, Grid, Card, CardContent, Button, 
  Box, Alert, Divider 
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { getSystemStatus } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import SearchIcon from '@mui/icons-material/Search';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import PeopleIcon from '@mui/icons-material/People';
import CategoryIcon from '@mui/icons-material/Category';
import CloudIcon from '@mui/icons-material/Cloud';

function Home() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const response = await getSystemStatus();
      setStats(response.data);
      setError(null);
    } catch (err) {
      console.error('Error loading stats:', err);
      setError('Failed to connect to backend API on port 8000');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner message="Loading system status..." />;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <Typography variant="h3" gutterBottom sx={{ fontWeight: 700 }}>
          ScholarLens
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          AI-powered platform for discovering and analyzing academic research papers
        </Typography>
        <Button
          variant="contained"
          size="large"
          startIcon={<SearchIcon />}
          onClick={() => navigate('/search')}
          sx={{ px: 4, py: 1.5 }}
        >
          Start Searching Papers
        </Button>
      </Box>

      <Divider sx={{ mb: 4 }} />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
          <Button size="small" onClick={loadStats} sx={{ ml: 2 }}>
            Retry
          </Button>
        </Alert>
      )}

      {stats && (
        <>
          <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
            System Overview
          </Typography>

          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <MenuBookIcon color="primary" sx={{ fontSize: 40, mr: 1 }} />
                    <Typography variant="h6">Papers</Typography>
                  </Box>
                  <Typography variant="h3" sx={{ mb: 1 }}>
                    {stats?.databases?.postgresql?.papers || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Research papers indexed
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <PeopleIcon color="secondary" sx={{ fontSize: 40, mr: 1 }} />
                    <Typography variant="h6">Authors</Typography>
                  </Box>
                  <Typography variant="h3" sx={{ mb: 1 }}>
                    {stats?.databases?.postgresql?.authors || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Unique researchers
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <CategoryIcon color="success" sx={{ fontSize: 40, mr: 1 }} />
                    <Typography variant="h6">Embeddings</Typography>
                  </Box>
                  <Typography variant="h3" sx={{ mb: 1 }}>
                    {stats?.databases?.faiss?.vectors || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    AI vector embeddings
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <CloudIcon 
                      color={stats?.status === 'operational' ? 'success' : 'error'} 
                      sx={{ fontSize: 40, mr: 1 }} 
                    />
                    <Typography variant="h6">Status</Typography>
                  </Box>
                  <Typography 
                    variant="h4" 
                    sx={{ 
                      mb: 1,
                      color: stats?.status === 'operational' ? 'success.main' : 'error.main' 
                    }}
                  >
                    {stats?.status === 'operational' ? '✓ Online' : '✗ Offline'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    System health
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Typography variant="h5" gutterBottom sx={{ mt: 6, mb: 3 }}>
            Platform Features
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    🔍 Semantic Search
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Find papers by meaning, not just keywords. AI understands context.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    🕸️ Knowledge Graph
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Explore connections between papers, authors, and topics.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    📊 Analytics
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Track research trends and collaboration networks.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}
    </Container>
  );
}

export default Home;  