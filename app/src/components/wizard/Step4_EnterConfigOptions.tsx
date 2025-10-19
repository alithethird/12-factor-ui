// src/components/wizard/Step4_EnterConfigOptions.tsx

import React, { useState } from 'react';
import { StepProps } from './stepProps';

// Define the new structure for a single config option
type ConfigType = 'string' | 'bool' | 'int' | 'float' | 'secret';

interface ConfigOption {
  key: string;
  type: ConfigType;
  value: string; // Default Value
  isOptional: boolean;
}

const Step4_EnterConfigOptions: React.FC<StepProps> = ({ onComplete }) => {
  // State for the list of options already added
  const [options, setOptions] = useState<ConfigOption[]>([]);
  
  // State for the inputs of the "new option" row
  const [newKey, setNewKey] = useState('');
  const [newType, setNewType] = useState<ConfigType>('string');
  const [newValue, setNewValue] = useState('');
  const [newIsOptional, setNewIsOptional] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Adds the new option from state to the main options list
   */
  const handleAddOption = () => {
    setError(null);
    
    // Basic validation
    if (!newKey.trim()) {
      setError('Config option name cannot be empty.');
      return;
    }
    if (options.some(opt => opt.key.toLowerCase() === newKey.trim().toLowerCase())) {
      setError('Key must be unique.');
      return;
    }

    // Check: Non-optional (required) configs cannot have a default value.
    if (!newIsOptional && newValue.trim() !== '') {
      setError('Required configs (non-optional) cannot have a default value.');
      return;
    }
    // --- END NEW VALIDATION ---

    // Add the new option to the list
    setOptions([
      ...options,
      { 
        key: newKey.trim(), 
        type: newType, 
        value: newValue.trim(),
        isOptional: newIsOptional
      }
    ]);

    // Reset the input fields
    setNewKey('');
    setNewValue('');
    setNewType('string');
    setNewIsOptional(false);
  };

  /**
   * Removes an option from the list by its key
   */
  const handleRemoveOption = (keyToRemove: string) => {
    setOptions(options.filter(opt => opt.key !== keyToRemove));
  };

  /**
   * Passes the final list of options to the parent wizard
   */
  const handleNext = () => {
    // Pass the full array of option objects
    onComplete({ configOptions: options });
  };

  return (
    <div className="step-content">
      <p>Enter any custom config options for your charm:</p>
      
      {/* --- RENDER THE LIST OF ADDED OPTIONS --- */}
      <div className="config-list">
        {options.length > 0 && (
          <div className="config-row header">
            <span>Key</span>
            <span>Type</span>
            <span>Optional</span>
            <span>Default Value</span>
            <span>Action</span>
          </div>
        )}
        {options.map((option) => (
          <div key={option.key} className="config-row">
            <span title={option.key}>{option.key}</span>
            <span>{option.type}</span>
            <span>{option.isOptional ? 'Yes' : 'No'}</span>
            <span title={option.value}>{option.value}</span>
            <button 
              onClick={() => handleRemoveOption(option.key)} 
              className="remove-btn"
            >
              Remove
            </button>
          </div>
        ))}
      </div>

      {/* --- INPUT ROW FOR ADDING NEW OPTIONS --- */}
      <div className="config-add-row">
        <input
          type="text"
          placeholder="Key (e.g., SECRET_KEY)"
          value={newKey}
          onChange={(e) => setNewKey(e.target.value)}
        />
        <select
          value={newType}
          onChange={(e) => setNewType(e.target.value as ConfigType)}
        >
          <option value="string">string</option>
          <option value="bool">bool</option>
          <option value="int">int</option>
          <option value="float">float</option>
          <option value="secret">secret</option>
        </select>
        
        <label className="config-checkbox-label">
          <input
            type="checkbox"
            checked={newIsOptional}
            onChange={(e) => setNewIsOptional(e.target.checked)}
          />
          Optional
        </label>
        
        <input
          type="text"
          placeholder="Default Value"
          value={newValue}
          onChange={(e) => setNewValue(e.target.value)}
        />
        <button
          type="button"
          onClick={handleAddOption}
          className="add-btn"
        >
          Add
        </button>
      </div>

      {error && <div className="error-message" style={{ marginTop: '1rem' }}>{error}</div>}

      <button onClick={handleNext} style={{ marginTop: '1.5rem' }}>
        Next: Get Files
      </button>
    </div>
  );
};

export default Step4_EnterConfigOptions;