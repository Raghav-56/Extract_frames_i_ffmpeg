document.addEventListener('DOMContentLoaded', function() {
    // Handle form submission on index page , jaha se upload hota hai koi sa v video (as hmne input and name video diya h)
    const form = document.getElementById('uploadForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(form);
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                if (!response.ok) throw new Error('Upload failed');
                window.location.href = '/results';
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });
    }

    // Handle results page //phle skeleton loading then merko result show ho jye jb load ho jye tb
    if (window.location.pathname === '/results') {
        const loadingSkeleton = document.getElementById('loading-skeleton');
        const framesList = document.getElementById('framesList');

        async function checkStatus() {
            try {
                const response = await fetch('/status');
                const data = await response.json();
                
                if (data.completed) {
                    // Hide skeleton, show results
                    loadingSkeleton.style.display = 'none';
                    framesList.style.display = 'flex';
                    
                    if (data.frames?.length) {
                        framesList.innerHTML = data.frames.map(frame => `
                            <div class="col-md-4 mb-3">
                                <div class="card">
                                    <img src="/frames/${frame}" class="card-img-top" alt="Frame">
                                </div>
                            </div>
                        `).join('');
                    }
                } else {
                    setTimeout(checkStatus, 1000);
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }

        checkStatus();
    }
});