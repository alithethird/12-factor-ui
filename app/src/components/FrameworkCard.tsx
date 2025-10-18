import * as React from 'react';
import { styled } from '@mui/material/styles';
import Card from '@mui/material/Card';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';

// Custom styled Card component for consistency
const LogoTitleItem = styled(Card)(({ theme }) => ({
    backgroundColor: '#fff',
    padding: theme.spacing(2), 
    textAlign: 'center',
    color: (theme.vars ?? theme).palette.text.secondary,
    height: '100%', 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    boxShadow: theme.shadows[3], 
    transition: 'transform 0.2s, box-shadow 0.2s', // Optional: for a subtle hover effect
    '&:hover': {
        transform: 'translateY(-2px)',
        boxShadow: theme.shadows[6],
    },
    ...theme.applyStyles('dark', {
        backgroundColor: '#1A2027',
    }),
}));

/**
 * Reusable component for displaying a framework logo and title.
 * @param {object} props
 * @param {string} props.name - The framework name (title).
 * @param {string} props.logo - The imported SVG logo source.
 * @param {string} props.alt - The alt text for the image.
 */
const FrameworkCard = ({ name, logo, alt }) => {
    return (
        <LogoTitleItem elevation={3}>
            <Stack 
                direction="column" 
                alignItems="center" 
                justifyContent="center" 
                spacing={1} 
                sx={{ width: '100%' }}
            >
                {/* Logo Image container to maintain consistent height */}
                <Box sx={{ height: 100, display: 'flex', alignItems: 'center' }}>
                    <img 
                        width="200"
                        height="100" 
                        src={logo} 
                        className={`${name}Logo`} 
                        alt={alt}
                        style={{ objectFit: 'contain' }}
                    />
                </Box>
                
                {/* Title Text */}
                <Typography variant="h6" component="p" color="text.primary">
                    {name}
                </Typography>
            </Stack>
        </LogoTitleItem>
    );
};

export default FrameworkCard;