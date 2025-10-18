// src/components/wizard/MultiStepWizard.tsx

import React, { useState } from 'react';
import AccordionStep from './AccordionStep';
import Step1_SelectFramework from './Step1_SelectFramework';
import Step2_UploadCode from './Step2_UploadCode';
import Step3_SelectIntegrations from './Step3_SelectIntegrations';
import Step4_EnterEnvVars from './Step4_EnterEnvVars';
import Step5_GetFiles from './Step5_GetFiles';
import './Wizard.css';

const MultiStepWizard: React.FC = () => {
  // State to track which step is currently open
  const [activeStep, setActiveStep] = useState(1);
  
  // State to hold all the data collected from the steps
  const [formData, setFormData] = useState({
    framework: '',
    frameworkName: '',
    source: null,
    sourceProjectName: '',
    integrations: [],
    envVars: {},
  });

  /**
   * This function is passed to each step.
   * When a step calls it, we update the main form data
   * and advance to the next step.
   */
  const handleStepComplete = (stepNumber: number, data: any) => {
    // You can update the main formData state here based on the step
    console.log(`Step ${stepNumber} complete with data:`, data);
    
    setFormData(prevData => ({
      ...prevData,
      ...data,
      sourceProjectName: data.source?.projectName || prevData.sourceProjectName,
    }));

    // Unfold the next step
    if (stepNumber < 5) {
      setActiveStep(stepNumber + 1);
    }
  };
/**
   * Allows the user to click on a previous step header to go back.
   * We only allow jumping to steps <= the current activeStep.
   */
  const handleSetStep = (targetStep: number) => {
    if (targetStep <= activeStep) {
      setActiveStep(targetStep);
    }
  };
  return (
    <div className="wizard-container">
      <AccordionStep
        title="1. Select Framework"
        stepNumber={1}
        activeStep={activeStep}
        onHeaderClick={handleSetStep}
        summaryTitle={
          formData.frameworkName 
            ? `Selected Framework: ${formData.frameworkName}` 
            : undefined
        }
      >
        <Step1_SelectFramework
          onComplete={(data) => handleStepComplete(1, data)}
        />
      </AccordionStep>

      <AccordionStep
        title="2. Enter GitHub Repository or Upload Code"
        stepNumber={2}
        activeStep={activeStep}
        onHeaderClick={handleSetStep}
        summaryTitle={
          formData.sourceProjectName 
            ? `Source: ${formData.sourceProjectName}` 
            : undefined
        }
      >
        <Step2_UploadCode
          onComplete={(data) => handleStepComplete(2, data)}
          framework={formData.framework}
        />
      </AccordionStep>

      <AccordionStep
        title="3. Select Integrations"
        stepNumber={3}
        activeStep={activeStep}
        onHeaderClick={handleSetStep}
      >
        <Step3_SelectIntegrations
          onComplete={(data) => handleStepComplete(3, data)}
        />
      </AccordionStep>

      <AccordionStep
        title="4. Enter Custom Environment Variables"
        stepNumber={4}
        activeStep={activeStep}
        onHeaderClick={handleSetStep}
      >
        <Step4_EnterEnvVars
          onComplete={(data) => handleStepComplete(4, data)}
        />
      </AccordionStep>

      <AccordionStep
        title="5. Get Resultant Rock and Charm Files"
        stepNumber={5}
        activeStep={activeStep}
        onHeaderClick={handleSetStep}
      >
        <Step5_GetFiles 
          allData={formData} // Pass all collected data to the final step
        />
      </AccordionStep>
    </div>
  );
};

export default MultiStepWizard;