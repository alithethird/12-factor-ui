// src/components/wizard/Step2_UploadCode.tsx

import React, { useState } from 'react';
import { StepProps } from './stepProps';

const Step2_UploadCode: React.FC<StepProps> = ({ onComplete }) => {
  const [repoUrl, setRepoUrl] = useState('');

  const handleNext = () => {
    onComplete({ source: { type: 'github', url: repoUrl } });
  };

  return (
    <div className="step-content">
      <label>
        GitHub Repository URL:
        <input
          type="text"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          placeholder="https://github.com/user/repo"
          style={{ width: '100%', marginTop: '0.5rem' }}
        />
      </label>
      <p>--- OR ---</p>
      <label>
        Upload code directory (.zip, .tar.gz):
        <input type="file" style={{ marginTop: '0.5rem' }} />
      </label>
      <button onClick={handleNext}>Next: Select Integrations</button>
    </div>
  );
};

export default Step2_UploadCode;