document.addEventListener('DOMContentLoaded', () => {
    const wizardContainer = document.getElementById('wizard-container');

    // --- Notification System ---
    const notificationContainer = document.createElement('div');
    notificationContainer.className = 'fixed bottom-5 right-5 z-50 space-y-2';
    document.body.appendChild(notificationContainer);

    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        const colors = {
            info: 'bg-blue-600',
            success: 'bg-green-600',
            error: 'bg-red-600',
        };
        notification.className = `w-64 text-white px-4 py-3 rounded-lg shadow-xl animate-fade-in ${colors[type]}`;
        notification.textContent = message;

        notificationContainer.prepend(notification);

        setTimeout(() => {
            notification.classList.add('animate-fade-out');
            notification.addEventListener('animationend', () => {
                notification.remove();
            });
        }, 4000);
    }

    // Inject CSS for notification animations
    const style = document.createElement('style');
    style.innerHTML = `
        @keyframes fade-in { from { opacity: 0; transform: translateX(100%); } to { opacity: 1; transform: translateX(0); } }
        .animate-fade-in { animation: fade-in 0.5s ease-out forwards; }
        @keyframes fade-out { from { opacity: 1; transform: translateX(0); } to { opacity: 0; transform: translateX(100%); } }
        .animate-fade-out { animation: fade-out 0.5s ease-in forwards; }
    `;
    document.head.appendChild(style);
    // --- END: Notification System ---

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
        wizardContainer.innerHTML = '';
        wizardContainer.appendChild(await renderSelectFramework());
        wizardContainer.appendChild(renderUploadProject());
        wizardContainer.appendChild(await renderSelectIntegrations());
        wizardContainer.appendChild(renderCustomizeConfigOptions());
        wizardContainer.appendChild(renderGenerate());
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

    async function renderSelectFramework() {
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

    function renderUploadProject() {
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
                let headers = { 'X-CSRFToken': csrftoken };

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
                    formData: { ...state.formData, jobId: result.jobId, source: { type: sourceType, projectName: result.projectName } },
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
        const summaryTitle = state.formData.source ? `Source: ${state.formData.source.projectName}` : null;
        return createAccordionStep('2. Provide Source Code', 2, summaryTitle, content);
    }

    async function renderSelectIntegrations() {
        const content = document.createElement('div');
        content.innerHTML = `<p class="mb-4">Select integrations:</p>`;
        const grid = document.createElement('div');
        grid.className = 'grid md:grid-cols-2 gap-4';

        try {
            const response = await fetch('/static/charmgen/integrations.json');
            if (!response.ok) throw new Error('Failed to load integrations.json.');
            const integrations = await response.json();

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


        } catch (err) {
            grid.innerHTML = `<p class="text-red-500">Error loading integrations: ${err.message}</p>`;

        }
        const nextBtn = document.createElement('button');
        nextBtn.className = 'mt-6 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700';
        nextBtn.textContent = 'Next: Config Options';
        nextBtn.addEventListener('click', () => setState({ activeStep: 4 }));


        content.appendChild(grid);
        content.appendChild(nextBtn);

        const summaryTitle = state.formData.integrations.length > 0 ? `${state.formData.integrations.length} Integration(s)` : null;
        return createAccordionStep('3. Select Integrations', 3, summaryTitle, content);

    }

    function renderCustomizeConfigOptions() {
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

    function renderGenerate() {
        const content = document.createElement('div');
        content.innerHTML = `
            <h4 class="text-xl font-bold">Generation Complete!</h4>
            <p class="my-4">All your selections are ready. Click the button to generate and download your packaged Rock and Charm files.</p>
            
            <!-- NEW: Live Log Panel -->
            <div id="log-panel" class="hidden my-4 border bg-gray-900 text-white font-mono text-sm rounded-lg h-64 overflow-y-auto p-4">
                <p class="text-gray-400">Waiting for output...</p>
            </div>

            <div id="error-msg-final" class="text-red-600 mb-4"></div>
            <button id="generate-btn" class="px-6 py-3 bg-green-600 text-white font-bold rounded hover:bg-green-700">Generate & Download Bundle</button>
        `;

        const handleGeneration = async () => {
            const btn = content.querySelector('#generate-btn');
            const errorMsg = content.querySelector('#error-msg-final');
            const logPanel = content.querySelector('#log-panel');

            btn.textContent = 'Starting...';
            btn.disabled = true;
            errorMsg.textContent = '';

            logPanel.classList.remove('hidden');
            logPanel.innerHTML = '<p class="text-gray-400">Starting generation process...</p>';

            try {
                const startResponse = await fetch('/api/start-generation/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
                    body: JSON.stringify(state.formData)
                });

                const startResult = await startResponse.json();
                if (!startResponse.ok) {
                    throw new Error(startResult.error || 'Failed to start generation.');
                }

                const taskId = startResult.taskId;
                showNotification('Generation process started...');
                btn.textContent = 'Generating...';

                const eventSource = new EventSource(`/api/generation-status/${taskId}/`);

                eventSource.onmessage = (event) => {
                    const data = JSON.parse(event.data);

                    // --- UPDATED LOGIC ---
                    // Differentiate between high-level status and raw logs
                    if (data.type === 'log') {
                        // If it's the first real log, clear the placeholder
                        if (logPanel.querySelector('.text-gray-400')) {
                            logPanel.innerHTML = '';
                        }
                        const logLine = document.createElement('p');
                        logLine.textContent = data.text;
                        logPanel.appendChild(logLine);
                        // Auto-scroll to the bottom
                        logPanel.scrollTop = logPanel.scrollHeight;
                    } else if (data.text) { // This is a status message
                        showNotification(data.text);
                    } else if (data.status) { // Legacy check
                        showNotification(data.status);
                    }

                    if (data.downloadUrl) {
                        showNotification('Bundle ready for download!', 'success');
                        window.location.href = data.downloadUrl;
                        eventSource.close();
                        btn.textContent = 'Generate & Download Bundle';
                        btn.disabled = false;
                        logPanel.classList.add('hidden');
                    }

                    if (data.error) {
                        eventSource.close();
                        const errorLine = document.createElement('p');
                        errorLine.className = 'text-red-400 font-bold';
                        errorLine.textContent = `ERROR: ${data.error}`;
                        logPanel.appendChild(errorLine);
                        logPanel.scrollTop = logPanel.scrollHeight;
                        throw new Error(data.error);
                    }
                };

                eventSource.onerror = (err) => {
                    console.error("EventSource failed:", err);
                    errorMsg.textContent = 'Error: Connection to server lost during generation.';
                    eventSource.close();
                    btn.textContent = 'Generate & Download Bundle';
                    btn.disabled = false;
                    logPanel.classList.add('hidden');
                };

            } catch (err) {
                errorMsg.textContent = `Error: ${err.message}`;
                showNotification(err.message, 'error');
                btn.textContent = 'Generate & Download Bundle';
                btn.disabled = false;
                logPanel.classList.add('hidden');
            }
        };

        content.querySelector('#generate-btn').addEventListener('click', handleGeneration);
        return createAccordionStep('5. Generate Files', 5, null, content);
    }

    // Initial render
    render();
});

