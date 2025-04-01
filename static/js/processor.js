import { showOverlayLoader, hideOverlayLoader, updateStatus } from './ui.js';
import { displayResults } from './frames.js';

/**
 * Set up file upload and drag-drop functionality
 */
export function setupFileUpload(elements) {
    elements.videoFileInput.addEventListener('change', event => handleFileSelection(event, elements));
    elements.uploadArea.addEventListener('dragover', event => handleDragOver(event, elements));
    elements.uploadArea.addEventListener('dragleave', event => handleDragLeave(event, elements));
    elements.uploadArea.addEventListener('drop', event => handleDrop(event, elements));
}

/**
 * Set up form submission
 */
export function setupFormSubmission(elements, state) {
    elements.extractForm.addEventListener('submit', event => handleFormSubmit(event, elements, state));
}

/**
 * Handle file selection
 */
function handleFileSelection(event, elements) {
    const file = event.target.files[0];
    if (file) {
        elements.selectedFileName.textContent = file.name;
        elements.uploadArea.classList.add('has-file');
    } else {
        elements.selectedFileName.textContent = '';
        elements.uploadArea.classList.remove('has-file');
    }
}

/**
 * Handle dragover event
 */
function handleDragOver(event, elements) {
    event.preventDefault();
    elements.uploadArea.classList.add('drag-over');
}

/**
 * Handle dragleave event
 */
function handleDragLeave(event, elements) {
    event.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
}

/**
 * Handle drop event
 */
function handleDrop(event, elements) {
    event.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
    
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('video/')) {
        elements.videoFileInput.files = event.dataTransfer.files;
        elements.selectedFileName.textContent = file.name;
        elements.uploadArea.classList.add('has-file');
    }
}

/**
 * Handle form submission
 */
function handleFormSubmit(event, elements, state) {
    event.preventDefault();
    
    // Validate input
    if (!elements.videoFileInput.files.length) {
        alert('Please select a video file');
        return;
    }
    
    // Show loader
    showOverlayLoader(elements);
    
    // Create form data
    const formData = new FormData(elements.extractForm);
    
    // Send request to upload endpoint
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        state.currentProcessingVideo = data.filename;
        startStatusCheck(elements, state);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error: ' + error.message);
        hideOverlayLoader(elements);
    });
}

/**
 * Start checking processing status
 */
function startStatusCheck(elements, state) {
    // Show status section and hide loader
    elements.statusSection.style.display = 'block';
    hideOverlayLoader(elements);
    
    // Set initial status
    updateStatus({
        is_processing: true,
        progress: 0,
        current_video: state.currentProcessingVideo
    }, elements);
    
    // Clear any existing interval
    if (state.statusCheckInterval) {
        clearInterval(state.statusCheckInterval);
    }
    
    // Start checking status every second
    state.statusCheckInterval = setInterval(() => checkStatus(elements, state), 1000);
}

/**
 * Check current processing status
 */
function checkStatus(elements, state) {
    fetch('/status')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            return response.json();
        })
        .then(status => {
            updateStatus(status, elements);
            
            // If processing is complete or errored, stop checking
            if (status.completed || status.error) {
                clearInterval(state.statusCheckInterval);
                
                // If completed, load frames after a short delay
                if (status.completed && status.frames && status.frames.length > 0) {
                    displayResults(status, elements, state);
                }
            }
        })
        .catch(error => {
            console.error('Error checking status:', error);
            // Don't stop checking on network errors
        });
}
