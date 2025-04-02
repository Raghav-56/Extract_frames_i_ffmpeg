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
        let selectedFrames =new Set();


        async function checkStatus() {
            try {
                const response = await fetch('/status');
                const data = await response.json();
                console.log('Status response:', data); // Add this line

                
                if (data.completed) {
                    // Hide skeleton, show results
                    loadingSkeleton.style.display = 'none';
                    framesList.style.display = 'flex';
                    document.getElementById('selectionControls').style.display = 'block';
                    
                    if (data.frames?.length) {
                        framesList.innerHTML = data.frames.map(frame => `
                            <div class="col-md-4 mb-3">
                                <div class="card frame-card" data-frame="${frame}">
                                <div class="card-img-overlay p-2">
                                <input type="checkbox" class="frame-selector form-check-input"/>
                                </div>    
                                <img src="/frames/${frame}" class="card-img-top" alt="Frame">
                                </div>
                            </div>
                        `).join('');

                            

                            //ab event listeners lgayege
                            setupFrameSelectors();


                    }
                } else {
                    setTimeout(checkStatus, 1000);
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }
/*------------------------------------------------------------------------------------------------------------------------------------*/ 

        function setupFrameSelectors(){
            const selectAllBtn=document.getElementById('selectAll');
            const deselectAllBtn=document.getElementById('deselectAll');
            const downloadSelectedBtn=document.getElementById('downloadSelected');
            const selectedCountSpan=document.getElementById('selectedCount');
            const checkboxes=document.querySelectorAll('.frame-selector');

            //for individul selection
            checkboxes.forEach(checkBox=>{
                checkBox.addEventListener('change',function(){
                    const frame=this.closest('.frame-card').dataset.frame;
                    if(this.checked){
                        selectedFrames.add(frame);
                        this.closest('.frame-card').classList.add('selected');
                    }
                    else{
                        selectedFrames.delete(frame);
                        this.closest('.frame-card').classList.remove('selected');
                    }
                    updateUI();
                })
            })

            //for select all and deselect all buttons

            selectAllBtn.addEventListener('click',function(){
                checkboxes.forEach(checkbox=>{
                    checkbox.checked=true;
                    const frame=checkbox.closest('.frame-card').dataset.frame;
                    selectedFrames.add(frame);
                    checkbox.closest('.frame-card').classList.add('selected');
                })
                updateUI();
            })
            deselectAllBtn.addEventListener('click',function(){
                checkboxes.forEach(checkbox=>{
                    checkbox.checked=false;
                    const frame=checkbox.closest('.frame-card').dataset.frame;
                    selectedFrames.delete(frame);
                    checkbox.closest('.frame-card').classList.remove('selected');
                })
                updateUI();
            })

            //for download selected frames button
            downloadSelectedBtn.addEventListener('click',function(){
                if(selectedFrames.size>0){
                    const framesToDownload = Array.from(selectedFrames);
                    
                    window.location.href=`/download_frames?frames=${encodeURIComponent(JSON.stringify(framesToDownload))}`;
                }
            })

            function updateUI(){
                selectedCountSpan.textContent=selectedFrames.size;
                downloadSelectedBtn.disabled=selectedFrames.size===0;
            }


        }   

        checkStatus();
    }
});