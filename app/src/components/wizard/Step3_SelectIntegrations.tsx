// src/components/wizard/Step3_SelectIntegrations.tsx

import React, { useState } from 'react';
import { StepProps } from './stepProps';

// Define the structure for an integration
interface Integration {
  id: string;
  name: string;
  description: string;
}

// List of supported integrations
const allIntegrations: Integration[] = [
  { id: 'prometheus', name: 'Prometheus', description: 'Monitoring & alerting' },
  { id: 'grafana', name: 'Grafana', description: 'Visualization dashboard' },
  { id: 'ingress', name: 'Ingress', description: 'Expose your app via HTTP/S' },
  { id: 'loki', name: 'Loki', description: 'Log aggregation system' },
  { id: 'postgresql', name: 'PostgreSQL', description: 'SQL database relation' },
  { id: 'tracing', name: 'Tracing', description: 'Distributed tracing (e.g., Jaeger)' },
  { id: 'smtp', name: 'SMTP', description: 'Email sending integration' },
  { id: 'openfga', name: 'OpenFGA', description: 'Fine-grained authorization' },
  { id: 'oidc', name: 'OIDC', description: 'User authentication' },
];

const Step3_SelectIntegrations: React.FC<StepProps> = ({ onComplete }) => {
  // Use state to track the array of selected integration IDs
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  /**
   * Toggles an integration ID in the state array.
   */
  const handleCheckboxChange = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) 
        ? prev.filter(i => i !== id) // Remove it
        : [...prev, id]               // Add it
    );
  };

  const handleNext = () => {
    // Pass the array of selected integration IDs
    onComplete({ integrations: selectedIds });
  };

  return (
    <div className="step-content">
      <p>Select the integrations you want to add to your application:</p>
      
      {/* --- NEW INTEGRATION GRID --- */}
      <div className="integration-grid">
        {allIntegrations.map((integration) => (
          // Use <label> for better accessibility; clicking text checks the box
          <label key={integration.id} className="integration-item">
            <input
              type="checkbox"
              checked={selectedIds.includes(integration.id)}
              onChange={() => handleCheckboxChange(integration.id)}
            />
            <div className="integration-info">
              <span className="integration-name">{integration.name}</span>
              <span className="integration-desc">{integration.description}</span>
            </div>
          </label>
        ))}
      </div>
      
      <button onClick={handleNext} style={{ marginTop: '1.5rem' }}>
        Next: Environment Variables
      </button>
    </div>
  );
};

export default Step3_SelectIntegrations;