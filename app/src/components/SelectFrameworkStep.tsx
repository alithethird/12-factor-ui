// SelectFrameworkStep.jsx
import * as React from 'react';
import { styled } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import FrameworkCard from './FrameworkCard'; // Your extracted card component
// Import assets... (DjangoLogo, FastAPILogo, etc.)

// ... (Define the frameworks array and styled components as before)

// Define the data for the frameworks
const frameworks = [
    { name: 'Django', logo: DjangoLogo, alt: 'Django logo' },
    { name: 'FastAPI', logo: FastAPILogo, alt: 'FastAPI logo' },
    { name: 'Flask', logo: FlaskLogo, alt: 'Flask logo' },
    { name: 'ExpressJS', logo: ExpressJSLogo, alt: 'ExpressJS logo' },
    { name: 'Go', logo: GoLogo, alt: 'Go logo' },
    { name: 'Spring Boot', logo: SpringBootLogo, alt: 'Spring Boot logo' },
];

/**
 * Step 1: Framework Selection Grid
 * @param {object} props
 * @param {string | null} props.selectedFramework - The currently selected framework name.
 * @param {function} props.onSelectFramework - Callback function to set the selected framework.
 */
export default function SelectFrameworkStep({ selectedFramework, onSelectFramework }) {
    const spacingValue = 3; 

    return (
        <Box sx={{ flexGrow: 1, p: spacingValue }}>
            <Typography variant="h5" gutterBottom>
                1. Select Framework
            </Typography>
            <Grid 
                container 
                rowSpacing={spacingValue} 
                columnSpacing={spacingValue} 
            > 
                {frameworks.map((framework) => (
                    <Grid item xs={12} sm={6} md={4} lg={4} key={framework.name}>
                        <div 
                            onClick={() => onSelectFramework(framework.name)}
                            style={{ 
                                cursor: 'pointer',
                                // Highlight the selected card
                                border: selectedFramework === framework.name ? '3px solid #E95420' : '3px solid transparent', 
                                borderRadius: '8px',
                                padding: '4px',
                                transition: 'border 0.2s',
                            }}
                        >
                            <FrameworkCard 
                                name={framework.name}
                                logo={framework.logo}
                                alt={framework.alt}
                            />
                        </div>
                    </Grid>
                ))}
            </Grid>
        </Box>
    );
}