import * as React from 'react';
import { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SelectFrameworkStep from './SelectFrameworkStep'; // Step 1

// --- Conceptual Step Components (Placeholders) ---
// Note: These must be actual React components in your final implementation.

const EnterSourceStep = ({ onNext, data, onDataChange }) => (
    <Box sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
            2. Enter GitHub Repository or Upload Code
        </Typography>
        {/* Example: Set dummy data and allow advancement */}
        <Button 
            variant="contained" 
            onClick={() => {
                onDataChange('source', 'https://github.com/my-app');
                onNext();
            }}
        >
            Simulate Source Entry & Next
        </Button>
    </Box>
);

const SelectIntegrationsStep = ({ onNext }) => (
    <Box sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
            3. Select Integrations (Databases, Monitoring, etc.)
        </Typography>
        <Button variant="contained" onClick={onNext}>
            Simulate Integrations & Next
        </Button>
    </Box>
);

const EnterEnvVarsStep = ({ onNext }) => (
    <Box sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
            4. Enter Custom Environment Variables
        </Typography>
        <Button variant="contained" onClick={onNext}>
            Simulate Env Vars & Next
        </Button>
    </Box>
);

const GetResultFilesStep = () => (
    <Box sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
            5. Get Resultant Rock and Charm Files
        </Typography>
        <Typography variant="body1">
            Charming process complete! Download files below.
        </Typography>
    </Box>
);

// --- Main Component ---

const initialCharmingData = {
    framework: null,
    source: null,
    integrations: [],
    envVars: {},
};

export default function CharmApplicationFlow() {
    const [activeStep, setActiveStep] = useState(0);
    const [charmingData, setCharmingData] = useState(initialCharmingData);
    
    // Total steps for checking completion
    const totalSteps = 5;

    // Handler to move to the next step
    const handleNext = () => {
        setActiveStep((prevActiveStep) => Math.min(prevActiveStep + 1, totalSteps - 1));
    };
    
    // Universal data update function
    const handleDataChange = (key, value) => {
        setCharmingData((prevData) => ({ ...prevData, [key]: value }));
    };

    // Special handler for Step 1 (Framework Selection)
    const handleFrameworkSelection = (frameworkName) => {
        handleDataChange('framework', frameworkName);
        
        // Auto-advance to the next step after selection
        handleNext(); 
    };
    
    // Define the content and title for each step
    const stepConfigs = [
        {
            title: '1. Select Framework',
            component: SelectFrameworkStep,
            props: {
                selectedFramework: charmingData.framework,
                onSelectFramework: handleFrameworkSelection,
            },
            isComplete: !!charmingData.framework,
        },
        {
            title: '2. Enter GitHub Repository or Upload Code',
            component: EnterSourceStep,
            props: {
                data: charmingData.source,
                onDataChange: handleDataChange,
                onNext: handleNext,
            },
            isComplete: !!charmingData.source, // Assuming 'source' is set upon completion
        },
        {
            title: '3. Select Integrations that you want',
            component: SelectIntegrationsStep,
            props: { onNext: handleNext },
            isComplete: activeStep > 2, // Simple check for conceptual step
        },
        {
            title: '4. Enter custom environment variables you want',
            component: EnterEnvVarsStep,
            props: { onNext: handleNext },
            isComplete: activeStep > 3, // Simple check for conceptual step
        },
        {
            title: '5. Get the resultant rock and charm files',
            component: GetResultFilesStep,
            props: {},
            isComplete: activeStep === totalSteps - 1, // Final step
        },
    ];


    return (
        <Box sx={{ width: '100%', maxWidth: 800, mx: 'auto', p: 4 }}>
            <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 4 }}>
                Charm Application Generator
            </Typography>
            
            {stepConfigs.map((step, index) => {
                const isExpanded = activeStep === index;
                const isFinalStep = index === totalSteps - 1;
                const StepComponent = step.component;
                
                return (
                    <Accordion 
                        key={index} 
                        expanded={isExpanded} 
                        // Disable interaction if the step is complete and not the final step
                        disabled={step.isComplete && !isFinalStep} 
                        sx={{ mt: 1 }}
                    >
                        <AccordionSummary
                            expandIcon={<ExpandMoreIcon />}
                            aria-controls={`panel${index}-content`}
                            id={`panel${index}-header`}
                            // Optionally, allow the user to click to re-open previous steps
                            onClick={() => {
                                if (step.isComplete && !isFinalStep) {
                                    setActiveStep(index);
                                }
                            }}
                        >
                            <Typography variant="h6" color={step.isComplete ? 'success.main' : 'text.primary'}>
                                {step.title} {step.isComplete && '✅'}
                            </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            {/* Render the specific step component */}
                            <StepComponent {...step.props} />
                        </AccordionDetails>
                    </Accordion>
                );
            })}
        </Box>
    );
}