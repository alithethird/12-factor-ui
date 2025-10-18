// src/App.tsx

import React from 'react';
import MultiStepWizard from './components/wizard/MultiStepWizard';

// Import your global styles and the wizard-specific styles
import './index.css';
import './components/wizard/Wizard.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>My Rock & Charm Generator</h1>
      </header>
      
      {/* The <main> tag will use App.css to center
        the wizard component on the page.
      */}
      <main>
        <MultiStepWizard />
      </main>
    </div>
  );
}

export default App;