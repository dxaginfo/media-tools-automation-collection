/**
 * SceneValidator Web Interface
 * JavaScript for the SceneValidator tool's browser interface
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const validationForm = document.getElementById('validationForm');
    const frameUpload = document.getElementById('frameUpload');
    const thumbnailsContainer = document.getElementById('thumbnails');
    const clearBtn = document.getElementById('clearBtn');
    const settingsForm = document.getElementById('settingsForm');
    const minContinuityScore = document.getElementById('minContinuityScore');
    const minContinuityScoreValue = document.getElementById('minContinuityScoreValue');
    const resultsCard = document.getElementById('resultsCard');
    const continuityScoreEl = document.getElementById('continuityScore');
    const compositionScoreEl = document.getElementById('compositionScore');
    const sceneQualityEl = document.getElementById('sceneQuality');
    const frameAnalysisEl = document.getElementById('frameAnalysis');
    const recommendationsListEl = document.getElementById('recommendationsList');
    const exportResultsBtn = document.getElementById('exportResults');
    
    // Sample data (for demonstration)
    let sampleData = null;
    
    // Update min continuity score display
    minContinuityScore.addEventListener('input', function() {
        minContinuityScoreValue.textContent = this.value;
    });
    
    // Handle file selection
    frameUpload.addEventListener('change', function(e) {
        thumbnailsContainer.innerHTML = '';
        
        if (this.files.length > 0) {
            for (let i = 0; i < this.files.length; i++) {
                const file = this.files[i];
                
                if (file.type.match('image.*')) {
                    const reader = new FileReader();
                    
                    reader.onload = (function(file, index) {
                        return function(e) {
                            const div = document.createElement('div');
                            div.className = 'thumbnail-container';
                            div.innerHTML = `
                                <img src="${e.target.result}" alt="Frame ${index + 1}">
                                <div class="thumbnail-number">${index + 1}</div>
                            `;
                            thumbnailsContainer.appendChild(div);
                        };
                    })(file, i);
                    
                    reader.readAsDataURL(file);
                }
            }
        }
    });
    
    // Clear button
    clearBtn.addEventListener('click', function() {
        validationForm.reset();
        thumbnailsContainer.innerHTML = '';
        resultsCard.style.display = 'none';
    });
    
    // Save settings
    settingsForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // In a real app, you would save these settings
        const apiKey = document.getElementById('apiKey').value;
        const projectId = document.getElementById('projectId').value;
        
        // Show confirmation
        alert('Settings saved successfully!');
    });
    
    // Validation form submission
    validationForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // In a real app, you would send the files to your API
        // For demo, we'll show sample results
        showSampleResults();
    });
    
    // Generate and show sample results
    function showSampleResults() {
        // Sample data for demonstration
        sampleData = {
            frame_count: 5,
            continuity_scores: [0.85, 0.68, 0.92, 0.75],
            average_continuity: 0.80,
            problem_frames: [2],
            composition_analyses: {
                first: {
                    composition_quality: "Good rule of thirds implementation",
                    lighting_assessment: "Balanced lighting with minor shadows",
                    depth_perspective: "Good depth with clear foreground/background",
                    overall_rating: 7.5
                },
                last: {
                    composition_quality: "Excellent framing and balance",
                    lighting_assessment: "Consistent lighting throughout",
                    depth_perspective: "Strong perspective with good spatial cues",
                    overall_rating: 8.2
                },
                problem_2: {
                    composition_quality: "Framing is off-center and unbalanced",
                    lighting_assessment: "Inconsistent lighting compared to previous frame",
                    depth_perspective: "Adequate depth cues",
                    overall_rating: 5.8
                }
            },
            validation_summary: {
                overall_continuity: 0.80,
                scene_quality: 0.76,
                issue_count: 1,
                recommendations: [
                    "Review continuity in frame 2 - lighting inconsistency",
                    "Consider adjusting framing in frame 2 for better balance",
                    "Overall composition is good across most frames"
                ]
            }
        };
        
        // Display results
        updateResults(sampleData);
    }
    
    // Update the results UI with data
    function updateResults(data) {
        // Show the results card
        resultsCard.style.display = 'block';
        
        // Update score metrics
        continuityScoreEl.textContent = (data.validation_summary.overall_continuity * 10).toFixed(1);
        // Average the composition scores from first and last frames
        const avgComposition = (parseFloat(data.composition_analyses.first.overall_rating) + 
                               parseFloat(data.composition_analyses.last.overall_rating)) / 2;
        compositionScoreEl.textContent = avgComposition.toFixed(1);
        sceneQualityEl.textContent = (data.validation_summary.scene_quality * 10).toFixed(1);
        
        // Apply color classes to scores
        applyScoreColor(continuityScoreEl, data.validation_summary.overall_continuity * 10);
        applyScoreColor(compositionScoreEl, avgComposition);
        applyScoreColor(sceneQualityEl, data.validation_summary.scene_quality * 10);
        
        // Build frame analysis
        frameAnalysisEl.innerHTML = '';
        
        // First frame analysis
        createFrameAnalysisCard(
            0, 
            'First Frame', 
            data.composition_analyses.first, 
            null,
            frameAnalysisEl
        );
        
        // Problem frames
        if (data.problem_frames.length > 0) {
            data.problem_frames.forEach(frameIndex => {
                const prevScore = frameIndex > 0 ? data.continuity_scores[frameIndex-1] : null;
                createFrameAnalysisCard(
                    frameIndex, 
                    `Problem Frame (${frameIndex+1})`, 
                    data.composition_analyses[`problem_${frameIndex+1}`],
                    prevScore,
                    frameAnalysisEl
                );
            });
        }
        
        // Last frame
        createFrameAnalysisCard(
            data.frame_count - 1, 
            'Last Frame', 
            data.composition_analyses.last, 
            data.continuity_scores[data.continuity_scores.length - 1],
            frameAnalysisEl
        );
        
        // Add recommendations
        recommendationsListEl.innerHTML = '';
        data.validation_summary.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.textContent = rec;
            recommendationsListEl.appendChild(li);
        });
    }
    
    // Create frame analysis card
    function createFrameAnalysisCard(index, title, analysis, continuityScore, container) {
        const card = document.createElement('div');
        card.className = 'frame-card';
        
        // Generate a sample image for demo (in a real app, this would be the actual frame)
        const imgSrc = `https://picsum.photos/seed/${index+1}/400/300`;
        
        let continuityHtml = '';
        if (continuityScore !== null) {
            // Position marker at percentage of width
            const markerPosition = continuityScore * 100;
            continuityHtml = `
                <div class="continuity-indicator">
                    <span class="me-2">Continuity:</span>
                    <div class="continuity-indicator-bar">
                        <div class="continuity-indicator-marker" style="left: ${markerPosition}%"></div>
                    </div>
                    <span class="ms-2 ${getScoreClass(continuityScore * 10)}">${(continuityScore * 10).toFixed(1)}</span>
                </div>
            `;
        }
        
        card.innerHTML = `
            <div class="frame-card-header">
                <h6 class="mb-0">${title}</h6>
                <span class="badge bg-secondary">Frame ${index + 1}</span>
            </div>
            <div class="frame-card-body">
                <img src="${imgSrc}" class="frame-preview" alt="Frame ${index + 1}">
                ${continuityHtml}
                <div class="mt-3">
                    <div><strong>Composition:</strong> ${analysis.composition_quality}</div>
                    <div><strong>Lighting:</strong> ${analysis.lighting_assessment}</div>
                    <div><strong>Depth/Perspective:</strong> ${analysis.depth_perspective}</div>
                    <div class="mt-2">
                        <strong>Overall Rating:</strong> 
                        <span class="${getScoreClass(analysis.overall_rating)}">
                            ${analysis.overall_rating}/10
                        </span>
                    </div>
                </div>
                <div class="detected-objects">
                    <span class="object-tag">Person</span>
                    <span class="object-tag">Chair</span>
                    <span class="object-tag ${index === 1 ? 'object-new' : ''}">Window</span>
                    <span class="object-tag ${index === 1 ? 'object-missing' : ''}">Table</span>
                </div>
                <div class="color-palette">
                    <div class="color-swatch" style="background-color: #7a5c58"></div>
                    <div class="color-swatch" style="background-color: #c7b299"></div>
                    <div class="color-swatch" style="background-color: #e8e8e6"></div>
                    <div class="color-swatch" style="background-color: #565264"></div>
                </div>
            </div>
        `;
        
        container.appendChild(card);
    }
    
    // Apply color class based on score
    function applyScoreColor(element, score) {
        element.className = getScoreClass(score);
    }
    
    // Get score CSS class
    function getScoreClass(score) {
        if (score >= 7.5) return 'score-high';
        if (score >= 6) return 'score-medium';
        return 'score-low';
    }
    
    // Export results
    exportResultsBtn.addEventListener('click', function() {
        if (!sampleData) return;
        
        // Create a JSON blob and download it
        const dataStr = JSON.stringify(sampleData, null, 2);
        const blob = new Blob([dataStr], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'scene_validation_results.json';
        a.click();
        
        URL.revokeObjectURL(url);
    });
});
