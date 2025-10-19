// src/components/wizard/Step4_EnterConfigOptions.tsx

import React, { useState } from 'react';
import { StepProps } from './stepProps';

type ConfigType = 'string' | 'bool' | 'int' | 'float' | 'secret';
// Define the structure for a single config option
interface ConfigOption {
  key: string;
  type: ConfigType;
  value: string; // Default Value
  isOptional: boolean; // NEW
}

const Step4_EnterConfigOptions: React.FC<StepProps> = ({ onComplete }) => {
  // State for the list of options already added
  const [options, setOptions] = useState<ConfigOption[]>([]);
  
  // State for the inputs of the "new option" row
  const [newKey, setNewKey] = useState('');
  const [newType, setNewType] = useState<ConfigType>('string');
  const [newValue, setNewValue] = useState('');
  const [newIsOptional, setNewIsOptional] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Adds the new option from state to the main options list
   */
  const handleAddOption = () => {
    setError(null);
    // Basic validation
    if (!newKey.trim()) {
      setError('Key cannot be empty.');
      return;
    }
    // Check for duplicate keys
    if (options.some(opt => opt.key.toLowerCase() === newKey.trim().toLowerCase())) {
      setError('Key must be unique.');
      return;
    }

    // Add the new option to the list
    setOptions([
      ...options,
      { 
        key: newKey.trim(), 
        type: newType, 
        value: newValue.trim(),
        isOptional: newIsOptional // NEW
      }
    ]);

    // Reset the input fields
    setNewKey('');
    setNewValue('');
    setNewType('string');
    setNewIsOptional(true);
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
    // We'll pass the array of objects as 'configOptions'
    // You can also transform this into an object map if you prefer
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
            <span>Optional</span> {/* NEW */}
            <span>Default Value</span>
            <span>Action</span>
          </div>
        )}
        {options.map((option) => (
          <div key={option.key} className="config-row">
            <span title={option.key}>{option.key}</span>
            <span>{option.type}</span>
            <span>{option.isOptional ? 'Yes' : 'No'}</span> {/* NEW */}
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
          <option value="secret">secret</option> {/* FIXED */}
        </select>
        
        {/* NEW CHECKBOX */}
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