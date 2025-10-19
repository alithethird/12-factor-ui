document.addEventListener('DOMContentLoaded', () => {
    const wizardContainer = document.getElementById('wizard-container');

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    let state = {
        activeStep: 1,
        formData: {
            framework: '',
            frameworkName: '',
            source: null,
            jobId: '',
            integrations: [],
            configOptions: [],
        }
    };

    function setState(newState) {
        state = { ...state, ...newState };
        render();
    }

    async function render() {
        wizardContainer.innerHTML = ''; // Clear previous state
        wizardContainer.appendChild(await renderStep1()); // Step 1 is async
        wizardContainer.appendChild(renderStep2());
        wizardContainer.appendChild(renderStep3());
        wizardContainer.appendChild(renderStep4());
        wizardContainer.appendChild(renderStep5());
    }

    function createAccordionStep(title, stepNumber, summaryTitle, contentEl) {
        const isCompleted = stepNumber < state.activeStep;
        const isActive = stepNumber === state.activeStep;
        const displayTitle = (isCompleted && summaryTitle) ? summaryTitle : title;

        const wrapper = document.createElement('div');
        wrapper.className = 'border-b border-gray-200';
        wrapper.innerHTML = `
            <div class="accordion-header p-4 cursor-pointer hover:bg-gray-50 ${isCompleted ? 'bg-green-50 text-green-700' : ''} ${isActive ? 'bg-blue-50' : ''}">
                <h3 class="text-lg font-semibold">${displayTitle} ${isCompleted ? '✓' : ''}</h3>
            </div>
            <div class="accordion-content ${isActive ? 'open' : ''}">
                <div class="p-6"></div>
            </div>
        `;

        wrapper.querySelector('.accordion-header').addEventListener('click', () => {
            if (stepNumber <= state.activeStep) {
                setState({ activeStep: stepNumber });
            }
        });

        wrapper.querySelector('.p-6').appendChild(contentEl);
        return wrapper;
    }

    // --- RENDER FUNCTIONS FOR EACH STEP ---

    async function renderStep1() {
        const content = document.createElement('div');
        content.innerHTML = `<p class="mb-4">Select your project's framework:</p>`;
        const grid = document.createElement('div');
        grid.className = 'grid grid-cols-2 md:grid-cols-4 gap-4';
        
        try {
            const response = await fetch('/static/charmgen/frameworks.json');
            if (!response.ok) throw new Error('Failed to load frameworks.json.');
            const frameworks = await response.json();

            frameworks.forEach(fw => {
                const card = document.createElement('div');
                card.className = `framework-card p-4 border-2 rounded-lg cursor-pointer text-center hover:border-blue-500 flex flex-col items-center justify-center space-y-2 ${state.formData.framework === fw.id ? 'selected' : ''}`;
                
                const img = document.createElement('img');
                img.src = fw.logo_url;
                img.alt = `${fw.name} Logo`;
                img.className = 'h-10 w-10 object-contain';
                card.appendChild(img);

                const span = document.createElement('span');
                span.textContent = fw.name;
                span.className = 'font-semibold';
                card.appendChild(span);

                card.addEventListener('click', () => {
                    setState({
                        formData: { ...state.formData, framework: fw.id, frameworkName: fw.name },
                        activeStep: 2
                    });
                });
                grid.appendChild(card);
            });
        } catch (err) {
            grid.innerHTML = `<p class="text-red-500">Error loading frameworks: ${err.message}</p>`;
        }
        
        content.appendChild(grid);
        
        const summaryTitle = state.formData.frameworkName ? `Framework: ${state.formData.frameworkName}` : null;
        return createAccordionStep('1. Select Framework', 1, summaryTitle, content);
    }

    function renderStep2() {
        const content = document.createElement('div');
        let sourceType = 'github';

        const updateView = () => {
            content.innerHTML = `
                <div class="flex border-b mb-4">
                    <button class="tab-btn py-2 px-4 ${sourceType === 'github' ? 'border-b-2 border-blue-500 font-semibold' : ''}" data-type="github">From GitHub</button>
                    <button class="tab-btn py-2 px-4 ${sourceType === 'upload' ? 'border-b-2 border-blue-500 font-semibold' : ''}" data-type="upload">Upload Archive</button>
                </div>
                <div class="space-y-4">
                    <div id="github-view" class="${sourceType === 'github' ? '' : 'hidden'}">
                        <label class="block font-medium">GitHub Repository URL:</label>
                        <input type="text" id="repoUrl" class="w-full p-2 border rounded" placeholder="https://github.com/user/repo">
                    </div>
                    <div id="upload-view" class="${sourceType === 'upload' ? '' : 'hidden'}">
                        <label class="block font-medium">Code Archive (.zip, .tar, .tar.gz):</label>
                        <input type="file" id="fileUpload" class="w-full p-2 border rounded" accept=".zip,.tar,.tar.gz">
                    </div>
                    <div id="error-msg" class="text-red-600"></div>
                    <button id="validate-btn" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Validate & Continue</button>
                </div>
            `;

            content.querySelectorAll('.tab-btn').forEach(btn => btn.addEventListener('click', (e) => {
                sourceType = e.target.dataset.type;
                updateView();
            }));
            
            content.querySelector('#validate-btn').addEventListener('click', handleValidation);
        };

        const handleValidation = async () => {
            const btn = content.querySelector('#validate-btn');
            const errorMsg = content.querySelector('#error-msg');
            btn.textContent = 'Validating...';
            btn.disabled = true;
            errorMsg.textContent = '';

            try {
                let response;
                let body;
                let headers = {'X-CSRFToken': csrftoken};

                if (sourceType === 'github') {
                    body = JSON.stringify({ repoUrl: content.querySelector('#repoUrl').value, framework: state.formData.framework });
                    headers['Content-Type'] = 'application/json';
                } else {
                    const file = content.querySelector('#fileUpload').files[0];
                    if (!file) throw new Error("Please select a file.");
                    body = new FormData();
                    body.append('file', file);
                    body.append('framework', state.formData.framework);
                }
                
                response = await fetch('/api/validate-source/', { method: 'POST', body, headers });
                const result = await response.json();
                if (!response.ok) throw new Error(result.error || 'Validation failed');
                
                setState({
                    formData: { ...state.formData, jobId: result.jobId, source: { type: sourceType, projectName: result.projectName }},
                    activeStep: 3
                });

            } catch (err) {
                errorMsg.textContent = `Error: ${err.message}`;
            } finally {
                btn.textContent = 'Validate & Continue';
                btn.disabled = false;
            }
        };
        
        updateView();
        const summaryTitle = state.formData.source ? `Source: ${state.formData.source.projectName}`: null;
        return createAccordionStep('2. Provide Source Code', 2, summaryTitle, content);
    }

    function renderStep3() {
        const integrations = [
            { id: 'prometheus', name: 'Prometheus', description: 'Monitoring & alerting' },
            { id: 'grafana', name: 'Grafana', description: 'Visualization dashboard' },
            { id: 'postgresql', name: 'PostgreSQL', description: 'SQL database relation' },
        ];
        const content = document.createElement('div');
        content.innerHTML = `<p class="mb-4">Select integrations:</p>`;
        const grid = document.createElement('div');
        grid.className = 'grid md:grid-cols-2 gap-4';

        integrations.forEach(item => {
            const label = document.createElement('label');
            label.className = 'flex items-start gap-3 p-4 border rounded-lg cursor-pointer';
            label.innerHTML = `
                <input type="checkbox" class="mt-1" data-id="${item.id}" ${state.formData.integrations.includes(item.id) ? 'checked' : ''}>
                <div>
                    <span class="font-semibold">${item.name}</span>
                    <p class="text-sm text-gray-600">${item.description}</p>
                </div>
            `;
            label.querySelector('input').addEventListener('change', (e) => {
                const id = e.target.dataset.id;
                const newIntegrations = e.target.checked
                    ? [...state.formData.integrations, id]
                    : state.formData.integrations.filter(i => i !== id);
                setState({ formData: { ...state.formData, integrations: newIntegrations } });
            });
            grid.appendChild(label);
        });

        const nextBtn = document.createElement('button');
        nextBtn.className = 'mt-6 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700';
        nextBtn.textContent = 'Next: Config Options';
        nextBtn.addEventListener('click', () => setState({ activeStep: 4 }));

        content.appendChild(grid);
        content.appendChild(nextBtn);
        
        const summaryTitle = state.formData.integrations.length > 0 ? `${state.formData.integrations.length} Integration(s)` : null;
        return createAccordionStep('3. Select Integrations', 3, summaryTitle, content);
    }

    function renderStep4() {
        const content = document.createElement('div');
        content.innerHTML = `<p class="mb-4">Add custom configuration options (Key, Type, Optional, Default Value).</p>
        <p class="text-gray-500 italic">This UI is abridged. Click Next to continue.</p>`;
        
        const nextBtn = document.createElement('button');
        nextBtn.className = 'mt-6 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700';
        nextBtn.textContent = 'Next: Get Files';
        nextBtn.addEventListener('click', () => setState({ activeStep: 5 }));
        content.appendChild(nextBtn);

        const summaryTitle = state.formData.configOptions.length > 0 ? `${state.formData.configOptions.length} Option(s)` : null;
        return createAccordionStep('4. Custom Config Options', 4, summaryTitle, content);
    }

    function renderStep5() {
        const content = document.createElement('div');
        content.innerHTML = `
            <h4 class="text-xl font-bold">Generation Complete!</h4>
            <p class="my-4">All your selections are ready. Click the button to generate and download your packaged Rock and Charm files.</p>
            <div id="error-msg-final" class="text-red-600 mb-4"></div>
            <button id="generate-btn" class="px-6 py-3 bg-green-600 text-white font-bold rounded hover:bg-green-700">Generate & Download Bundle</button>
        `;
        
        const handleGeneration = async () => {
            const btn = content.querySelector('#generate-btn');
            const errorMsg = content.querySelector('#error-msg-final');
            btn.textContent = 'Generating...';
            btn.disabled = true;
            errorMsg.textContent = '';
            
            try {
                const response = await fetch('/api/generate-bundle/', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken 
                    },
                    body: JSON.stringify(state.formData)
                });
                
                if (response.headers.get('Content-Type') === 'application/zip') {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = 'rock-and-charm-bundle.zip';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    a.remove();
                } else {
                    const result = await response.json();
                    throw new Error(result.error || 'Generation failed');
                }

            } catch(err) {
                errorMsg.textContent = `Error: ${err.message}`;
            } finally {
                btn.textContent = 'Generate & Download Bundle';
                btn.disabled = false;
            }
        };

        content.querySelector('#generate-btn').addEventListener('click', handleGeneration);
        return createAccordionStep('5. Generate Files', 5, null, content);
    }
    
    // Initial render
    render();
});
