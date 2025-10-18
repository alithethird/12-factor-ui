// src/components/wizard/Step5_GetFiles.tsx

import React, { useEffect } from 'react';

interface GetFilesProps {
  allData: any; // Receives all data from the parent wizard
}

const Step5_GetFiles: React.FC<GetFilesProps> = ({ allData }) => {
  
  useEffect(() => {
    // When this step becomes active, you could trigger
    // the final build/generation process.
    console.log('Generating files with all collected data:', allData);
    // ... trigger API call ...
  }, [allData]);

  return (
    <div className="step-content">
      <h4>Generation Complete!</h4>
      <p>Your files are ready to be downloaded.</p>
      
      {/* Show summary based on allData */}
      <pre style={{ background: '#f4f4f4', padding: '1rem', borderRadius: '4px' }}>
        {JSON.stringify(allData, null, 2)}
      </pre>

      <div style={{ display: 'flex', gap: '1rem' }}>
        <button type="button">Download Rockfile</button>
        <button type="button">Download Charm Files (.zip)</button>
      </div>
    </div>
  );
};

export default Step5_GetFiles;