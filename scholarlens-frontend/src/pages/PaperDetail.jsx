import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Container, Typography, Box, Chip, Button, Card, CardContent, 
  Divider, Alert, Grid, Paper 
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import CategoryIcon from '@mui/icons-material/Category';
import PersonIcon from '@mui/icons-material/Person';
import { getPaperById } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

function PaperDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPaper();
  }, [id]);

  const loadPaper = async () => {
    try {
      setLoading(true);
      const response = await getPaperById(id);
      setPaper(response.data);
      setError(null);
    } catch (err) {
      console.error('Error loading paper:', err);
      setError(`Failed to load paper. ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner message="Loading paper details..." />;
  
  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
        <Button 
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(-1)}
          variant="outlined"
        >
          Go Back
        </Button>
      </Container>
    );
  }
  
  if (!paper) return null;

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Button 
        startIcon={<ArrowBackIcon />} 
        onClick={() => navigate(-1)}
        sx={{ mb: 2 }}
        variant="outlined"
      >
        Back to Results
      </Button>

      <Card elevation={3}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
            {paper.title}
          </Typography>

          <Box sx={{ mb: 3, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {paper.primary_category && (
              <Chip 
                icon={<CategoryIcon />}
                label={paper.primary_category} 
                color="primary" 
              />
            )}
            {paper.published_date && (
              <Chip 
                icon={<CalendarTodayIcon />}
                label={paper.published_date} 
                variant="outlined" 
              />
            )}
            {paper.arxiv_id && (
              <Chip 
                label={`arXiv: ${paper.arxiv_id}`} 
                variant="outlined" 
                clickable
                onClick={() => window.open(`https://arxiv.org/abs/${paper.arxiv_id}`, '_blank')}
                onDelete={() => window.open(`https://arxiv.org/abs/${paper.arxiv_id}`, '_blank')}
                deleteIcon={<OpenInNewIcon />}
              />
            )}
          </Box>

          <Divider sx={{ my: 3 }} />

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <PersonIcon sx={{ mr: 1 }} /> Authors
            </Typography>
            <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
              <Typography variant="body1">
                {paper.authors?.map(a => a.name || a).join(', ') || 'No authors listed'}
              </Typography>
            </Paper>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Abstract
            </Typography>
            <Typography 
              variant="body1" 
              paragraph 
              sx={{ 
                textAlign: 'justify', 
                lineHeight: 1.8,
                color: 'text.secondary'
              }}
            >
              {paper.abstract || 'No abstract available.'}
            </Typography>
          </Box>

          {(paper.methods?.length > 0 || paper.datasets?.length > 0) && (
            <>
              <Divider sx={{ my: 3 }} />
              <Grid container spacing={3}>
                {paper.methods?.length > 0 && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>
                      Methods Used
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {paper.methods.map((method, idx) => (
                        <Chip 
                          key={idx} 
                          label={method} 
                          color="primary"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Grid>
                )}

                {paper.datasets?.length > 0 && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>
                      Datasets Used
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {paper.datasets.map((dataset, idx) => (
                        <Chip 
                          key={idx} 
                          label={dataset} 
                          color="secondary"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Grid>
                )}
              </Grid>
            </>
          )}

          {paper.categories?.length > 0 && (
            <>
              <Divider sx={{ my: 3 }} />
              <Typography variant="h6" gutterBottom>
                All Categories
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {paper.categories.map((cat, idx) => (
                  <Chip 
                    key={idx} 
                    label={cat} 
                    size="small"
                    variant="outlined" 
                  />
                ))}
              </Box>
            </>
          )}

          <Divider sx={{ my: 3 }} />
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">
                Paper ID
              </Typography>
              <Typography variant="body1">
                {paper.paper_id}
              </Typography>
            </Grid>
            {paper.citation_count !== undefined && (
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Citations
                </Typography>
                <Typography variant="body1">
                  {paper.citation_count}
                </Typography>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>
    </Container>
  );
}

export default PaperDetail;