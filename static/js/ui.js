/**
 * Initialize the UI components
 */
export function initUI(elements) {
    // Fetch configuration
    fetch('/config')
        .then(response => response.json())
        .then(config => {
            document.getElementById('quality').value = config.quality;
            
            if (config.supported_formats) {
                const formatInfo = document.getElementById('supportedFormats');
                if (formatInfo) {
                    formatInfo.textContent = config.supported_formats.join(', ');
                }
            }
        })
        .catch(error => {
            console.error('Error fetching configuration:', error);
        });
}

/**
 * Show overlay loader
 */
export function showOverlayLoader(elements) {
    elements.overlayLoader.style.display = 'flex';
}

/**
 * Hide overlay loader
 */
export function hideOverlayLoader(elements) {
    elements.overlayLoader.style.display = 'none';
}

/**
 * Update status display
 */
export function updateStatus(status, elements) {
    // Update progress bar
    elements.progressBarFill.style.width = `${status.progress}%`;
    
    // Update current video
    if (status.current_video) {
        elements.currentVideo.textContent = status.current_video;
    }
    
    // Update processing time if available
    if (status.elapsed_seconds !== undefined) {
        const minutes = Math.floor(status.elapsed_seconds / 60);
        const seconds = Math.floor(status.elapsed_seconds % 60);
        elements.processingTime.textContent = `Processing time: ${minutes}m ${seconds}s`;
    }
    
    // Update status indicators
    if (status.error) {
        elements.statusIndicator.className = 'status-indicator error';
        elements.statusText.textContent = 'Error';
        elements.statusMessage.textContent = status.error;
    } else if (status.completed) {
        elements.statusIndicator.className = 'status-indicator success';
        elements.statusText.textContent = 'Completed';
        elements.statusMessage.textContent = `Successfully extracted ${status.frames ? status.frames.length : 0} frames.`;
    } else if (status.is_processing) {
        elements.statusIndicator.className = 'status-indicator processing';
        elements.statusText.textContent = 'Processing...';
        elements.statusMessage.textContent = `Extracting frames... ${status.progress}%`;
    }
    
    // Update metadata if available
    if (status.metadata) {
        elements.metadataSection.style.display = 'block';
        elements.metadataTable.innerHTML = '';
        
        Object.entries(status.metadata).forEach(([key, value]) => {
            const row = document.createElement('tr');
            const keyCell = document.createElement('td');
            const valueCell = document.createElement('td');
            
            keyCell.textContent = key.replace(/_/g, ' ');
            valueCell.textContent = value;
            
            row.appendChild(keyCell);
            row.appendChild(valueCell);
            elements.metadataTable.appendChild(row);
        });
    } else {
        elements.metadataSection.style.display = 'none';
    }
}
