// src/components/wizard/Step2_UploadCode.tsx

import React, { useState } from 'react';
import { StepProps } from './stepProps';
// We NO LONGER import the service classes

type SourceType = 'github' | 'upload';

// --- IMPORTANT ---
// Replace this with your actual backend server's address
const API_BASE_URL = 'http://localhost:8080'; // Example: for a local server

const Step2_UploadCode: React.FC<StepProps> = ({ onComplete, framework }) => {
  const [sourceType, setSourceType] = useState<SourceType>('github');
  const [repoUrl, setRepoUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  /**
   * Main submit handler that decides which API to call
   */
  const handleSubmit = async () => {
    if (!framework) {
      setError('Framework not selected. Please go back to Step 1.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      let result;
      if (sourceType === 'github') {
        result = await handleGithubSubmit();
      } else {
        result = await handleUploadSubmit();
      }

      // If successful, complete the step
      onComplete({ source: result.sourceData });

    } catch (err: any) {
      console.error(err);
      setError(err.message || 'An unknown error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handles the API call for GitHub validation
   */
  const handleGithubSubmit = async () => {
    if (!repoUrl) throw new Error('Please enter a GitHub URL.');

    const response = await fetch(`${API_BASE_URL}/api/validate-github`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        repoUrl: repoUrl,
        framework: framework,
      }),
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
      throw new Error(result.error || 'GitHub validation failed.');
    }

    return result; // { success: true, sourceData: { ... } }
  };

  /**
   * Handles the API call for file upload validation
   */
  const handleUploadSubmit = async () => {
    if (!file) throw new Error('Please select a file to upload.');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('framework', framework as string); // Add framework to the form data

    const response = await fetch(`${API_BASE_URL}/api/validate-upload`, {
      method: 'POST',
      body: formData,
      // NOTE: Do NOT set 'Content-Type' for FormData,
      // the browser sets it automatically with the correct boundary
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
      throw new Error(result.error || 'File validation failed.');
    }

    return result; // { success: true, sourceData: { ... } }
  };


  return (
    <div className="step-content">
      {/* --- Tab Selector (No Change) --- */}
      <div className="tab-container">
        <button
          className={`tab-button ${sourceType === 'github' ? 'active' : ''}`}
          onClick={() => setSourceType('github')}
        >
          From GitHub
        </button>
        <button
          className={`tab-button ${sourceType === 'upload' ? 'active' : ''}`}
          onClick={() => setSourceType('upload')}
        >
          Upload .zip / .tar.gz
        </button>
      </div>

      {/* --- Tab Content (No Change) --- */}
      <div className="tab-content">
        {sourceType === 'github' ? (
          <div className="input-group">
            <label htmlFor="repoUrl">GitHub Repository URL:</label>
            <input
              id="repoUrl"
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/user/repo"
              disabled={isLoading}
            />
          </div>
        ) : (
          <div className="input-group">
            <label htmlFor="fileUpload">Code Archive:</label>
            <input
              id="fileUpload"
              type="file"
              accept=".zip,.tar.gz,.tar"
              onChange={handleFileChange}
              disabled={isLoading}
            />
          </div>
        )}
      </div>

      {/* --- Error Display (No Change) --- */}
      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* --- Action Button (No Change) --- */}
      <button onClick={handleSubmit} disabled={isLoading} style={{ marginTop: '1rem' }}>
        {isLoading ? 'Validating...' : 'Validate & Continue'}
      </button>
    </div>
  );
};

export default Step2_UploadCode;