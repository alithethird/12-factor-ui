// src/components/wizard/Step3_SelectIntegrations.tsx

import React from 'react';
import { StepProps } from './stepProps';

const Step3_SelectIntegrations: React.FC<StepProps> = ({ onComplete }) => {
  // Logic to manage selected integrations (e.g., useState)

  const handleNext = () => {
    // Pass an array of selected integration names
    onComplete({ integrations: ['database-postgres', 'logging-loki'] });
  };

  return (
    <div className="step-content">
      <p>Select integrations you want to add:</p>
      {/* Add checkboxes or a multi-select component here */}
      <label>
        <input type="checkbox" defaultChecked /> PostgreSQL Database
      </label>
      <label>
        <input type="checkbox" defaultChecked /> Loki Logging
      </label>
      <button onClick={handleNext}>Next: Environment Variables</button>
    </div>
  );
};

export default Step3_SelectIntegrations;