document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const extractForm = document.getElementById('extractForm');
    const uploadOption = document.getElementById('uploadOption');
    const pathOption = document.getElementById('pathOption');
    const uploadSection = document.getElementById('uploadSection');
    const pathSection = document.getElementById('pathSection');
    const videoFileInput = document.getElementById('videoFile');
    const selectedFileName = document.getElementById('selectedFileName');
    const uploadArea = document.getElementById('uploadArea');
    const statusSection = document.getElementById('statusSection');
    const framesSection = document.getElementById('framesSection');
    const refreshFramesBtn = document.getElementById('refreshFrames');
    const downloadAllFramesBtn = document.getElementById('downloadAllFrames');
    const framesContainer = document.getElementById('framesContainer');
    const overlayLoader = document.getElementById('overlayLoader');
    const framePreview = document.getElementById('framePreview');
    const closePreviewBtn = document.getElementById('closePreview');
    const previewImage = document.getElementById('previewImage');
    const prevFrameBtn = document.getElementById('prevFrame');
    const nextFrameBtn = document.getElementById('nextFrame');
    const downloadFrameBtn = document.getElementById('downloadFrame');
    const currentFrameNumber = document.getElementById('currentFrameNumber');
    const totalFrames = document.getElementById('totalFrames');
    
    // Status elements
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const currentVideo = document.getElementById('currentVideo');
    const progressBarFill = document.getElementById('progressBarFill');
    const processingTime = document.getElementById('processingTime');
    const statusMessage = document.getElementById('statusMessage');
    const metadataSection = document.getElementById('metadataSection');
    const metadataTable = document.getElementById('metadataTable');
    
    // Variables
    let currentProcessingVideo = null;
    let statusCheckInterval = null;
    let currentFrames = [];
    let currentFrameIndex = 0;
    
    // Initialize with default settings
    init();
    
    // Event listeners for radio buttons
    uploadOption.addEventListener('change', toggleSourceSections);
    pathOption.addEventListener('change', toggleSourceSections);
    
    // File selection event
    videoFileInput.addEventListener('change', handleFileSelection);
    
    // Drag and drop events
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // Form submission
    extractForm.addEventListener('submit', handleFormSubmit);
    
    // Frame related events
    refreshFramesBtn.addEventListener('click', loadFrames);
    downloadAllFramesBtn.addEventListener('click', downloadAllFrames);
    
    // Preview events
    closePreviewBtn.addEventListener('click', closePreview);
    prevFrameBtn.addEventListener('click', showPreviousFrame);
    nextFrameBtn.addEventListener('click', downloadCurrentFrame);
    downloadFrameBtn.addEventListener('click', downloadCurrentFrame);
    
    /**
     * Initialize the application
     */
    function init() {
        // Fetch initial configuration
        fetch('/config')
            .then(response => response.json())
            .then(config => {
                // Set default output directory
                document.getElementById('outputRoot').value = config.output_root;
                document.getElementById('quality').value = config.quality;
                
                // Create default folders
                fetch('/create_default_folders', {
                    method: 'POST'
                });
            })
            .catch(error => {
                console.error('Error fetching configuration:', error);
            });
    }
    
    /**
     * Toggle visibility of source sections based on selected option
     */
    function toggleSourceSections() {
        if (uploadOption.checked) {
            uploadSection.style.display = 'block';
            pathSection.style.display = 'none';
        } else {
            uploadSection.style.display = 'none';
            pathSection.style.display = 'block';
        }
    }
    
    /**
     * Handle file selection through the file input
     */
    function handleFileSelection(event) {
        const file = event.target.files[0];
        if (file) {
            selectedFileName.textContent = file.name;
            uploadArea.classList.add('has-file');
        } else {
            selectedFileName.textContent = '';
            uploadArea.classList.remove('has-file');
        }
    }
    
    /**
     * Handle dragover event
     */
    function handleDragOver(event) {
        event.preventDefault();
        uploadArea.classList.add('drag-over');
    }
    
    /**
     * Handle dragleave event
     */
    function handleDragLeave(event) {
        event.preventDefault();
        uploadArea.classList.remove('drag-over');
    }
    
    /**
     * Handle drop event
     */
    function handleDrop(event) {
        event.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        const file = event.dataTransfer.files[0];
        if (file && file.type.startsWith('video/')) {
            videoFileInput.files = event.dataTransfer.files;
            selectedFileName.textContent = file.name;
            uploadArea.classList.add('has-file');
        }
    }
    
    /**
     * Handle form submission
     */
    function handleFormSubmit(event) {
        event.preventDefault();
        
        // Show overlay loader
        overlayLoader.style.display = 'flex';
        
        const formData = new FormData(extractForm);
        
        // Determine if we're uploading or using local path
        if (uploadOption.checked) {
            // Check if file is selected
            if (!videoFileInput.files.length) {
                alert('Please select a video file to upload');
                overlayLoader.style.display = 'none';
                return;
            }
            
            // Upload the file
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                currentProcessingVideo = data.filename;
                startStatusCheck();
            })
            .catch(error => {
                alert('Error: ' + error.message);
                overlayLoader.style.display = 'none';
            });
        } else {
            // Check if path is provided
            const videoPath = document.getElementById('videoPath').value;
            if (!videoPath) {
                alert('Please enter a video path');
                overlayLoader.style.display = 'none';
                return;
            }
            
            // Process local video
            fetch('/process', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                currentProcessingVideo = data.filename;
                startStatusCheck();
            })
            .catch(error => {
                alert('Error: ' + error.message);
                overlayLoader.style.display = 'none';
            });
        }
    }
    
    /**
     * Start checking processing status
     */
    function startStatusCheck() {
        // Show status section
        statusSection.style.display = 'block';
        
        // Hide overlay loader
        overlayLoader.style.display = 'none';
        
        // Set initial status
        updateStatus({
            is_processing: true,
            progress: 0,
            current_video: currentProcessingVideo
        });
        
        // Start checking status
        statusCheckInterval = setInterval(checkStatus, 1000);
    }
    
    /**
     * Check current processing status
     */
    function checkStatus() {
        fetch('/status')
            .then(response => response.json())
            .then(status => {
                updateStatus(status);
                
                // If completed, stop checking
                if (status.completed || status.error) {
                    clearInterval(statusCheckInterval);
                    
                    if (status.completed) {
                        // Load frames after completion
                        setTimeout(loadFrames, 1000);
                    }
                }
            })
            .catch(error => {
                console.error('Error checking status:', error);
            });
    }
    
    /**
     * Update status display
     */
    function updateStatus(status) {
        // Update progress bar
        progressBarFill.style.width = `${status.progress}%`;
        
        // Update current video
        if (status.current_video) {
            currentVideo.textContent = status.current_video;
        }
        
        // Update processing time if available
        if (status.elapsed_seconds !== undefined) {
            const minutes = Math.floor(status.elapsed_seconds / 60);
            const seconds = status.elapsed_seconds % 60;
            processingTime.textContent = `Processing time: ${minutes}m ${seconds}s`;
        }
        
        // Update status text and class
        if (status.error) {
            statusIndicator.className = 'status-indicator error';
            statusText.textContent = 'Error';
            statusMessage.textContent = status.error;
        } else if (status.completed) {
            statusIndicator.className = 'status-indicator success';
            statusText.textContent = 'Completed';
            statusMessage.textContent = `Successfully extracted ${status.frame_count || 0} frames.`;
        } else {
            statusIndicator.className = 'status-indicator processing';
            statusText.textContent = 'Processing...';
            statusMessage.textContent = `Extracting frames... ${status.progress}%`;
        }
        
        // Update metadata if available
        if (status.metadata) {
            metadataSection.style.display = 'block';
            metadataTable.innerHTML = '';
            
            Object.entries(status.metadata).forEach(([key, value]) => {
                const row = document.createElement('tr');
                const keyCell = document.createElement('td');
                const valueCell = document.createElement('td');
                
                keyCell.textContent = key.replace(/_/g, ' ');
                valueCell.textContent = value;
                
                row.appendChild(keyCell);
                row.appendChild(valueCell);
                metadataTable.appendChild(row);
            });
        } else {
            metadataSection.style.display = 'none';
        }
    }
    
    /**
     * Load frames from the server
     */
    function loadFrames() {
        // Show overlay loader
        overlayLoader.style.display = 'flex';
        
        fetch('/frames')
            .then(response => response.json())
            .then(data => {
                // Hide overlay loader
                overlayLoader.style.display = 'none';
                
                // Show frames section
                framesSection.style.display = 'block';
                
                if (data.length === 0) {
                    framesContainer.innerHTML = '<p>No frames found.</p>';
                    return;
                }
                
                // Clear container
                framesContainer.innerHTML = '';
                
                // Process each video's frames
                data.forEach(videoData => {
                    const videoSection = document.createElement('div');
                    videoSection.className = 'video-frames-section';
                    
                    const videoTitle = document.createElement('h3');
                    videoTitle.textContent = videoData.video_name;
                    videoSection.appendChild(videoTitle);
                    
                    const frameInfo = document.createElement('p');
                    frameInfo.textContent = `${videoData.frame_count} frames extracted`;
                    videoSection.appendChild(frameInfo);
                    
                    const framesGrid = document.createElement('div');
                    framesGrid.className = 'frames-grid';
                    
                    videoData.frames.forEach((framePath, index) => {
                        const frameItem = document.createElement('div');
                        frameItem.className = 'frame-item';
                        
                        const frameImg = document.createElement('img');
                        frameImg.src = `/frames/${framePath}`;
                        frameImg.alt = `Frame ${index + 1}`;
                        frameImg.loading = 'lazy';
                        
                        frameItem.appendChild(frameImg);
                        framesGrid.appendChild(frameItem);
                        
                        // Add click event to open preview
                        frameItem.addEventListener('click', () => {
                            openFramePreview(videoData.frames, index);
                        });
                    });
                    
                    videoSection.appendChild(framesGrid);
                    framesContainer.appendChild(videoSection);
                });
            })
            .catch(error => {
                // Hide overlay loader
                overlayLoader.style.display = 'none';
                console.error('Error loading frames:', error);
                framesContainer.innerHTML = '<p>Error loading frames. Please try again.</p>';
            });
    }
    
    /**
     * Open frame preview
     */
    function openFramePreview(frames, index) {
        currentFrames = frames;
        currentFrameIndex = index;
        
        // Show preview
        framePreview.style.display = 'flex';
        
        // Update image and details
        updateFramePreview();
    }
    
    /**
     * Update frame preview content
     */
    function updateFramePreview() {
        previewImage.src = `/frames/${currentFrames[currentFrameIndex]}`;
        currentFrameNumber.textContent = currentFrameIndex + 1;
        totalFrames.textContent = currentFrames.length;
        
        // Update button states
        prevFrameBtn.disabled = currentFrameIndex === 0;
        nextFrameBtn.disabled = currentFrameIndex === currentFrames.length - 1;
    }
    
    /**
     * Show previous frame
     */
    function showPreviousFrame() {
        if (currentFrameIndex > 0) {
            currentFrameIndex--;
            updateFramePreview();
        }
    }
    
    /**
     * Show next frame
     */
    function showNextFrame() {
        if (currentFrameIndex < currentFrames.length - 1) {
            currentFrameIndex++;
            updateFramePreview();
        }
    }
    
    /**
     * Close frame preview
     */
    function closePreview() {
        framePreview.style.display = 'none';
    }
    
    /**
     * Download current frame
     */
    function downloadCurrentFrame() {
        const framePath = currentFrames[currentFrameIndex];
        const link = document.createElement('a');
        link.href = `/frames/${framePath}`;
        link.download = framePath.split('/').pop();
        link.click();
    }
    
    /**
     * Download all frames as zip
     */
    function downloadAllFrames() {
        // Get video path from first video section
        const videoSection = document.querySelector('.video-frames-section');
        if (!videoSection) {
            alert('No frames available to download');
            return;
        }
        
        const videoName = videoSection.querySelector('h3').textContent;
        
        // Create download link
        const link = document.createElement('a');
        link.href = `/download_frames?video_path=${videoName}`;
        link.download = `${videoName}_frames.zip`;
        link.click();
    }
});
