// src/components/wizard/Step1_SelectFramework.tsx

import React, { useState } from 'react';
import { StepProps } from './stepProps';

// --- NEW SVG IMPORTS ---
// You'll need to create these SVG files in src/assets/logos/
import FlaskLogo from '../../assets/logos/flask.svg';
import DjangoLogo from '../../assets/logos/django.svg';
import FastAPILogo from '../../assets/logos/fastapi.svg';
import GoLogo from '../../assets/logos/go.svg';
import ExpressJSLogo from '../../assets/logos/expressjs.svg';
import SpringBootLogo from '../../assets/logos/spring-boot.svg';


// Define the structure for a framework
interface Framework {
  id: string;
  name: string;
  logoSrc: string;
}

// --- NEW FRAMEWORKS DATA ---
const frameworks: Framework[] = [
  { id: 'flask', name: 'Flask', logoSrc: FlaskLogo },
  { id: 'django', name: 'Django', logoSrc: DjangoLogo },
  { id: 'fastapi', name: 'FastAPI', logoSrc: FastAPILogo },
  { id: 'go', name: 'Go', logoSrc: GoLogo },
  { id: 'expressjs', name: 'Express.js', logoSrc: ExpressJSLogo },
  { id: 'springboot', name: 'Spring Boot', logoSrc: SpringBootLogo },
];

const Step1_SelectFramework: React.FC<StepProps> = ({ onComplete }) => {
  const [selectedFrameworkId, setSelectedFrameworkId] = useState<string | null>(null);

const handleFrameworkSelect = (framework: Framework) => {
    setSelectedFrameworkId(framework.id);
// Pass both the ID and the display Name up to the parent
    onComplete({ 
      framework: framework.id,
      frameworkName: framework.name  // <-- This is the new piece of data
    });
  };

  return (
    <div className="step-content">
      <p>Please select your project's framework:</p>
      
      {/* --- NEW FRAMEWORK GRID --- */}
      <div className="framework-grid">
        {frameworks.map((framework) => (
          <div
            key={framework.id}
            className={`framework-card ${selectedFrameworkId === framework.id ? 'selected' : ''}`}
            onClick={() => handleFrameworkSelect(framework)}
          >
            <img src={framework.logoSrc} alt={`${framework.name} Logo`} className="framework-logo" />
            <span className="framework-title">{framework.name}</span>
          </div>
        ))}
      </div>
      
    </div>
  );
};

export default Step1_SelectFramework;