// src/components/wizard/AccordionStep.tsx

import React from 'react';

interface AccordionStepProps {
    title: string;
    stepNumber: number;
    activeStep: number;
    children: React.ReactNode;
    onHeaderClick: (stepNumber: number) => void;
    summaryTitle?: string;
}

const AccordionStep: React.FC<AccordionStepProps> = ({
    title,
    stepNumber,
    activeStep,
    children,
    onHeaderClick,
    summaryTitle,
}) => {

    // A step is active if its number matches the parent's activeStep state
    const isActive = stepNumber === activeStep;

    // A step is completed if it's before the current active step
    const isCompleted = stepNumber < activeStep;

    // A step is clickable if it's the active one or has been completed.
    // This prevents clicking on future, disabled steps.
    const isClickable = stepNumber <= activeStep;
    let headerClass = 'accordion-header';
    if (isActive) headerClass += ' active';
    if (isCompleted) headerClass += ' completed';
    if (isClickable) headerClass += ' clickable';
// Determine which title to display.
  // Use the summaryTitle if the step is completed AND summaryTitle was provided.
  // Otherwise, fall back to the default title.
  const displayTitle = (isCompleted && summaryTitle) ? summaryTitle : title;
    return (
        <div className="accordion-step">
            <div
                className={headerClass}
                onClick={() => onHeaderClick(stepNumber)}
            >
                <h3>{displayTitle} {isCompleted && '✓'}</h3>
            </div>

            {/* The 'accordion-content' div uses CSS to 'unfold'
        by transitioning max-height from 0 to 600px.
      */}
            <div className={`accordion-content ${isActive ? 'open' : ''}`}>
                <div className="accordion-content-padding">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default AccordionStep;