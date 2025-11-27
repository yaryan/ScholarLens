import React from 'react';
import { 
  Card, CardContent, Typography, Chip, Box, Button, 
  CardActions 
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArticleIcon from '@mui/icons-material/Article';
import PersonIcon from '@mui/icons-material/Person';

function PaperCard({ paper }) {
  const navigate = useNavigate();

  const handleViewDetails = () => {
    navigate(`/paper/${paper.paper_id}`);
  };

  return (
    <Card 
      sx={{ 
        mb: 2, 
        transition: 'box-shadow 0.3s',
        '&:hover': { boxShadow: 6 } 
      }}
    >
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 500 }}>
          {paper.title}
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <PersonIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary">
            {paper.authors?.join(', ') || 'Unknown authors'}
          </Typography>
        </Box>

        <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
          {paper.abstract 
            ? (paper.abstract.length > 250 
                ? paper.abstract.substring(0, 250) + '...' 
                : paper.abstract)
            : 'No abstract available.'}
        </Typography>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          {paper.primary_category && (
            <Chip label={paper.primary_category} size="small" color="primary" />
          )}
          {paper.published_date && (
            <Chip label={paper.published_date} size="small" variant="outlined" />
          )}
          {paper.similarity_score && (
            <Chip 
              label={`Match: ${(paper.similarity_score * 100).toFixed(0)}%`} 
              size="small" 
              color="success"
              variant="outlined"
            />
          )}
        </Box>
      </CardContent>

      <CardActions>
        <Button 
          size="small" 
          variant="contained"
          startIcon={<ArticleIcon />}
          onClick={handleViewDetails}
        >
          View Details
        </Button>
      </CardActions>
    </Card>
  );
}

export default PaperCard;