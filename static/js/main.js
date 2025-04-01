import { initUI, showOverlayLoader, hideOverlayLoader } from './ui.js';
import { setupFileUpload, setupFormSubmission } from './processor.js';
import { setupFrameHandlers } from './frames.js';

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    const elements = {
        // Core elements
        extractForm: document.getElementById('extractForm'),
        videoFileInput: document.getElementById('videoFile'),
        selectedFileName: document.getElementById('selectedFileName'),
        uploadArea: document.getElementById('uploadArea'),
        extractButton: document.getElementById('extractButton'),
        
        // Status elements
        statusSection: document.getElementById('statusSection'),
        statusIndicator: document.getElementById('statusIndicator'),
        statusText: document.getElementById('statusText'),
        currentVideo: document.getElementById('currentVideo'),
        progressBarFill: document.getElementById('progressBarFill'),
        processingTime: document.getElementById('processingTime'),
        statusMessage: document.getElementById('statusMessage'),
        metadataSection: document.getElementById('metadataSection'),
        metadataTable: document.getElementById('metadataTable'),
        
        // Frame elements
        framesSection: document.getElementById('framesSection'),
        framesContainer: document.getElementById('framesContainer'),
        downloadAllFramesBtn: document.getElementById('downloadAllFrames'),
        framePreview: document.getElementById('framePreview'),
        closePreviewBtn: document.getElementById('closePreview'),
        previewImage: document.getElementById('previewImage'),
        prevFrameBtn: document.getElementById('prevFrame'),
        nextFrameBtn: document.getElementById('nextFrame'),
        downloadFrameBtn: document.getElementById('downloadFrame'),
        currentFrameNumber: document.getElementById('currentFrameNumber'),
        totalFrames: document.getElementById('totalFrames'),
        
        // Overlay loader
        overlayLoader: document.getElementById('overlayLoader')
    };
    
    // State object shared between modules
    const state = {
        currentProcessingVideo: null,
        statusCheckInterval: null,
        currentFrames: [],
        currentFrameIndex: 0
    };
    
    // Initialize UI components
    initUI(elements);
    
    // Set up file upload and form submission
    setupFileUpload(elements);
    setupFormSubmission(elements, state);
    
    // Set up frame display and preview functionality
    setupFrameHandlers(elements, state);
});
