document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const extractForm = document.getElementById('extractForm');
    const statusSection = document.getElementById('statusSection');
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const currentVideo = document.getElementById('currentVideo');
    const statusMessage = document.getElementById('statusMessage');
    const refreshFramesBtn = document.getElementById('refreshFrames');
    const framesContainer = document.getElementById('framesContainer');
    const framePreview = document.getElementById('framePreview');
    const previewTitle = document.getElementById('previewTitle');
    const previewImage = document.getElementById('previewImage');
    const closePreview = document.getElementById('closePreview');

    // Load current configuration
    fetchConfig();

    // Event listeners
    extractForm.addEventListener('submit', startProcessing);
    refreshFramesBtn.addEventListener('click', fetchFrames);
    closePreview.addEventListener('click', () => {
        framePreview.style.display = 'none';
    });

    // Functions
    function fetchConfig() {
        fetch('/config')
            .then(response => response.json())
            .then(config => {
                document.getElementById('outputRoot').value = config.output_root || '';
                document.getElementById('quality').value = config.quality || 2;
                
                const formatSelect = document.getElementById('outputFormat');
                for(let i = 0; i < formatSelect.options.length; i++) {
                    if(formatSelect.options[i].value === config.output_format) {
                        formatSelect.selectedIndex = i;
                        break;
                    }
                }
            })
            .catch(error => console.error('Error fetching config:', error));
    }

    function startProcessing(e) {
        e.preventDefault();
        
        const formData = new FormData(extractForm);
        
        fetch('/process', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            statusSection.style.display = 'block';
            startStatusPolling();
        })
        .catch(error => {
            console.error('Error starting processing:', error);
            showStatus('error', 'Failed to start processing', error.message);
        });
    }

    function startStatusPolling() {
        const checkStatus = () => {
            fetch('/status')
                .then(response => response.json())
                .then(status => {
                    if (status.is_processing) {
                        showStatus('processing', 'Processing', `Currently processing: ${status.current_video}`);
                        setTimeout(checkStatus, 2000);  // Poll every 2 seconds
                    } else if (status.completed) {
                        showStatus('completed', 'Completed', 'Processing completed successfully');
                        fetchFrames();  // Update frames list when done
                    } else if (status.error) {
                        showStatus('error', 'Error', `Processing failed: ${status.error}`);
                    }
                })
                .catch(error => {
                    console.error('Error checking status:', error);
                    showStatus('error', 'Error', 'Failed to check processing status');
                });
        };
        
        checkStatus();  // Start the polling
    }

    function showStatus(type, text, message) {
        statusSection.style.display = 'block';
        statusIndicator.className = 'status-indicator ' + type;
        statusText.textContent = text;
        statusMessage.textContent = message || '';
    }

    function fetchFrames() {
        fetch('/frames')
            .then(response => response.json())
            .then(frames => {
                if (frames.error) {
                    framesContainer.innerHTML = `<p>Error: ${frames.error}</p>`;
                    return;
                }
                
                if (frames.length === 0) {
                    framesContainer.innerHTML = '<p>No frames extracted yet.</p>';
                    return;
                }
                
                let html = '';
                frames.forEach(video => {
                    html += `
                        <div class="frame-card" onclick="showVideoFrames('${video.path}')">
                            <img src="/frames/${video.sample_frame}" alt="${video.video_name}" class="frame-image">
                            <div class="frame-info">
                                <strong>${video.video_name}</strong>
                                <p>${video.frame_count} frames</p>
                            </div>
                        </div>
                    `;
                });
                
                framesContainer.innerHTML = html;
            })
            .catch(error => {
                console.error('Error fetching frames:', error);
                framesContainer.innerHTML = '<p>Error loading frames.</p>';
            });
    }

    // Make showVideoFrames globally accessible
    window.showVideoFrames = function(videoPath) {
        fetch(`/frames?video_path=${encodeURIComponent(videoPath)}`)
            .then(response => response.json())
            .then(data => {
                // Implementation depends on how your backend returns individual frames
                // This is a simplified version assuming a different API structure
                previewTitle.textContent = videoPath.split('/').pop();
                if (data.sample_frame) {
                    previewImage.src = `/frames/${data.sample_frame}`;
                    framePreview.style.display = 'block';
                }
            })
            .catch(error => console.error('Error fetching video frames:', error));
    };

    // Show preview when clicking on a frame
    document.addEventListener('click', function(e) {
        if (e.target.closest('.frame-image')) {
            const src = e.target.src;
            previewImage.src = src;
            previewTitle.textContent = src.split('/').pop();
            framePreview.style.display = 'block';
        }
    });

    // Initial frames load
    fetchFrames();
});
