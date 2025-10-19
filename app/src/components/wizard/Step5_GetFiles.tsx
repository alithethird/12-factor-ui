// src/components/wizard/Step5_GetFiles.tsx

import React, { useState } from 'react';

interface GetFilesProps {
  allData: any; // Receives all collected data from the parent wizard
}

// --- IMPORTANT ---
// Replace this with your actual backend server's address
const API_BASE_URL = 'http://localhost:8080';

const Step5_GetFiles: React.FC<GetFilesProps> = ({ allData }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setIsLoading(true);
    setError(null);
    console.log('Sending data to server:', allData);

    try {
      const response = await fetch(`${API_BASE_URL}/api/generate-files`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(allData),
      });

      // If the response is not OK, it's an error (e.g., 500)
      if (!response.ok) {
        // Try to parse the error JSON from the server
        const errData = await response.json();
        throw new Error(errData.error || `Server error: ${response.statusText}`);
      }

      // --- File Download Logic ---
      // The response is a zip file (blob)
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      // Get filename from response header, or use a default
      const disposition = response.headers.get('content-disposition');
      let filename = 'rock-and-charm-bundle.zip';
      if (disposition && disposition.indexOf('attachment') !== -1) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        const matches = filenameRegex.exec(disposition);
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
        }
      }
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      // --- End File Download Logic ---

    } catch (err: any) {
      console.error(err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="step-content">
      <h4>Generation Complete!</h4>
      <p>All your selections are ready. Click the button to generate and download your packaged Rock and Charm files.</p>
      
      {/* Show summary based on allData */}
      <pre style={{ background: '#f4f4f4', padding: '1rem', borderRadius: '4px', maxHeight: '200px', overflowY: 'auto' }}>
        {JSON.stringify(allData, null, 2)}
      </pre>

      <button onClick={handleGenerate} disabled={isLoading}>
        {isLoading ? 'Generating...' : 'Generate & Download Bundle'}
      </button>

      {error && (
        <div className="error-message" style={{ marginTop: '1rem' }}>
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
};

export default Step5_GetFiles;