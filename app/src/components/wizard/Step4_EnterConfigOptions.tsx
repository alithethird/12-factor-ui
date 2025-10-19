// src/components/wizard/Step4_EnterConfigOptions.tsx

import React from 'react';
import { StepProps } from './stepProps';

const Step4_EnterConfigOptions: React.FC<StepProps> = ({ onComplete }) => {
  // Logic to manage a list of key-value pairs

  const handleNext = () => {
    onComplete({ envVars: { DB_USER: 'admin', SECRET_KEY: '...' } });
  };

  return (
    <div className="step-content">
      <p>Enter any custom config options:</p>
      {/* Add a key-value pair editor component here */}
      <div>
        <input type="text" placeholder="Key (e.g., SECRET_KEY)" />
        <input type="text" placeholder="Value" />
        <button type="button" style={{ marginLeft: '0.5rem', background: '#6c757d' }}>Add</button>
      </div>
      <button onClick={handleNext}>Next: Get Files</button>
    </div>
  );
};

export default Step4_EnterConfigOptions;