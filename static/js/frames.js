/**
 * Set up frame handlers
 */
export function setupFrameHandlers(elements, state) {
    elements.downloadAllFramesBtn.addEventListener('click', () => downloadAllFrames(state));
    elements.closePreviewBtn.addEventListener('click', () => closePreview(elements));
    elements.prevFrameBtn.addEventListener('click', () => showPreviousFrame(elements, state));
    elements.nextFrameBtn.addEventListener('click', () => showNextFrame(elements, state));
    elements.downloadFrameBtn.addEventListener('click', () => downloadCurrentFrame(state));
}

/**
 * Display extraction results
 */
export function displayResults(status, elements, state) {
    // Show frames section
    elements.framesSection.style.display = 'block';
    
    if (!status.frames || status.frames.length === 0) {
        elements.framesContainer.innerHTML = '<p>No frames were extracted.</p>';
        return;
    }
    
    // Set up the frames data
    const framesData = {
        video_name: status.current_video || 'Unknown Video',
        frames: status.frames,
        frame_count: status.frames.length
    };
    
    // Display frames
    displayFrames(framesData, elements, state);
}

/**
 * Display frames in the UI
 */
function displayFrames(videoData, elements, state) {
    // Clear the container
    elements.framesContainer.innerHTML = '';
    
    // Create header
    const header = document.createElement('div');
    header.className = 'frames-header';
    
    const title = document.createElement('h3');
    title.textContent = videoData.video_name;
    header.appendChild(title);
    
    const info = document.createElement('p');
    info.textContent = `${videoData.frame_count} frames extracted`;
    header.appendChild(info);
    
    elements.framesContainer.appendChild(header);
    
    // Create frames grid
    const grid = document.createElement('div');
    grid.className = 'frames-grid';
    
    if (Array.isArray(videoData.frames) && videoData.frames.length > 0) {
        videoData.frames.forEach((framePath, index) => {
            const frameItem = document.createElement('div');
            frameItem.className = 'frame-item';
            
            // Create thumbnail with frame number
            const frameImg = document.createElement('img');
            const path = framePath.startsWith('/') ? framePath.substring(1) : framePath;
            frameImg.src = `/frames/${path}`;
            frameImg.alt = `Frame ${index + 1}`;
            frameImg.loading = 'lazy';
            
            // Error handling for images
            frameImg.onerror = function() {
                this.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="70" viewBox="0 0 100 70"><rect fill="%23f0f0f0" width="100" height="70"/><text x="50%" y="50%" font-family="sans-serif" font-size="12" text-anchor="middle">Error</text></svg>';
                this.alt = 'Error loading frame';
            };
            
            frameItem.appendChild(frameImg);
            
            // Add frame number label
            const frameNumber = document.createElement('div');
            frameNumber.className = 'frame-number';
            frameNumber.textContent = index + 1;
            frameItem.appendChild(frameNumber);
            
            // Add click event to open preview
            frameItem.addEventListener('click', () => {
                openFramePreview(videoData.frames, index, elements, state);
            });
            
            grid.appendChild(frameItem);
        });
    } else {
        grid.innerHTML = '<p class="no-frames">No frames available to display.</p>';
    }
    
    elements.framesContainer.appendChild(grid);
}

/**
 * Open frame preview
 */
function openFramePreview(frames, index, elements, state) {
    state.currentFrames = frames;
    state.currentFrameIndex = index;
    elements.framePreview.style.display = 'flex';
    updateFramePreview(elements, state);
}

/**
 * Update frame preview content
 */
function updateFramePreview(elements, state) {
    const framePath = state.currentFrames[state.currentFrameIndex];
    const path = framePath.startsWith('/') ? framePath.substring(1) : framePath;
    elements.previewImage.src = `/frames/${path}`;
    elements.previewImage.onload = () => {
        // Only update numbers after image loads
        elements.currentFrameNumber.textContent = state.currentFrameIndex + 1;
        elements.totalFrames.textContent = state.currentFrames.length;
        
        // Update button states
        elements.prevFrameBtn.disabled = state.currentFrameIndex === 0;
        elements.nextFrameBtn.disabled = state.currentFrameIndex === state.currentFrames.length - 1;
    };
    
    elements.previewImage.onerror = () => {
        elements.previewImage.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300"><rect fill="%23f0f0f0" width="400" height="300"/><text x="50%" y="50%" font-family="sans-serif" font-size="18" text-anchor="middle">Error loading image</text></svg>';
        console.error(`Failed to load image: ${path}`);
    };
}

/**
 * Show previous frame
 */
function showPreviousFrame(elements, state) {
    if (state.currentFrameIndex > 0) {
        state.currentFrameIndex--;
        updateFramePreview(elements, state);
    }
}

/**
 * Show next frame
 */
function showNextFrame(elements, state) {
    if (state.currentFrameIndex < state.currentFrames.length - 1) {
        state.currentFrameIndex++;
        updateFramePreview(elements, state);
    }
}

/**
 * Close frame preview
 */
function closePreview(elements) {
    elements.framePreview.style.display = 'none';
}

/**
 * Download current frame
 */
function downloadCurrentFrame(state) {
    if (!state.currentFrames || state.currentFrameIndex < 0 || state.currentFrameIndex >= state.currentFrames.length) {
        alert('No frame selected');
        return;
    }
    
    const framePath = state.currentFrames[state.currentFrameIndex];
    const path = framePath.startsWith('/') ? framePath.substring(1) : framePath;
    const link = document.createElement('a');
    link.href = `/frames/${path}`;
    link.download = path.split('/').pop();
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Download all frames as zip
 */
function downloadAllFrames(state) {
    if (!state.currentProcessingVideo) {
        alert('No video has been processed');
        return;
    }
    
    // Create download link
    const link = document.createElement('a');
    link.href = `/download_frames?video_path=${encodeURIComponent(state.currentProcessingVideo)}`;
    link.download = `${state.currentProcessingVideo}_frames.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
