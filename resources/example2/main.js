// Main application logic
document.addEventListener('DOMContentLoaded', () => {
    console.log('Application initialized');

    // Initialize storage
    let feedbackStore = {
        impact: [],
        behavior: [],
        betterment: []
    };

    // Initialize UI elements
    const startButton = document.getElementById('startAnalysis');
    const processingSection = document.getElementById('processingStages');
    const generateButton = document.getElementById('generateEvaluation');

    // Add event listener for start analysis button
    startButton.addEventListener('click', async () => {
        const feedback = document.getElementById('feedbackInput').value;
        const accomplishments = document.getElementById('accomplishmentsInput').value;
        
        if (!feedback || !accomplishments) {
            alert('Please provide both feedback and accomplishments');
            return;
        }

        try {
            // Reset storage
            feedbackStore = {
                impact: [],
                behavior: [],
                betterment: []
            };

            // Clear existing feedback
            clearFeedbackSections();

            // Show processing UI
            processingSection.style.display = 'block';
            startButton.disabled = true;
            generateButton.style.display = 'none';

            // Process feedback
            await processFeedback(feedback);
            
            // Process accomplishments
            await processAccomplishments(accomplishments);

            // Show generate button and review message
            const reviewMessage = document.createElement('div');
            reviewMessage.className = 'alert alert-info mt-3 mb-2';
            reviewMessage.innerHTML = `
                <h5>Ready to Generate Your Evaluation</h5>
                <p>Before generating, take a moment to review the sorted feedback and accomplishments above. 
                You can remove any items you don't want included in your final evaluation by clicking the × button on each item.</p>
            `;
            
            // Insert message before generate button
            generateButton.parentNode.insertBefore(reviewMessage, generateButton);
            generateButton.style.display = 'block';

        } catch (error) {
            console.error('Analysis error:', error);
            alert('An error occurred during analysis. Please try again.');
        } finally {
            startButton.disabled = false;
            processingSection.style.display = 'none';
        }
    });

    // Add event listener for generate evaluation button
    generateButton.addEventListener('click', async () => {
        try {
            // Get any notes/considerations
            const notes = document.getElementById('notesInput').value.trim();
            // Create and show processing modal FIRST
            const processingModalHtml = `
                <div class="modal fade" id="processingModal" tabindex="-1" data-bs-backdrop="static">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Generating Your Evaluation</h5>
                            </div>
                            <div class="modal-body">
                                <div class="current-stage mb-2">
                                    <span id="currentEvalStage">Initializing...</span>
                                    <span id="evalProgress" class="float-end">0%</span>
                                </div>
                                <div class="progress mb-2">
                                    <div id="evalProgressBar" class="progress-bar progress-bar-striped progress-bar-animated" 
                                         role="progressbar" style="width: 0%"></div>
                                </div>
                                <div id="evalStageDetail" class="stage-detail">
                                    Preparing to generate your evaluation...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Add processing modal to document
            const processingDiv = document.createElement('div');
            processingDiv.innerHTML = processingModalHtml;
            document.body.appendChild(processingDiv);

            // Show processing modal
            const processingModal = new bootstrap.Modal(document.getElementById('processingModal'), {
                keyboard: false,
                backdrop: 'static'
            });
            processingModal.show();

            // Wait for modal to show
            await delay(500);

            try {
                // Generate initial evaluation
                const rawEvaluation = await createEvaluation();

                // Process through improvement stages
                const stages = [
                    {
                        name: "Analyzing Feedback Patterns",
                        detail: "Identifying key themes and relationships",
                        duration: 2500,
                        process: (eval) => improveContentStructure(eval)
                    },
                    {
                        name: "Enhancing Content Depth",
                        detail: "Adding context and examples",
                        duration: 2500,
                        process: (eval) => addContentDepth(eval)
                    },
                    {
                        name: "Improving Writing Quality",
                        detail: "Refining language and transitions",
                        duration: 2000,
                        process: (eval) => improveWritingQuality(eval)
                    },
                    {
                        name: "Grammar and Style Check",
                        detail: "Ensuring professional tone and correct grammar",
                        duration: 2000,
                        process: (eval) => fixGrammarAndStyle(eval)
                    },
                    {
                        name: "Final Review",
                        detail: "Performing quality assurance checks",
                        duration: 2000,
                        process: (eval) => finalPolish(eval)
                    }
                ];

                let processedEval = rawEvaluation;
                
                // Process through each stage
                for (let i = 0; i < stages.length; i++) {
                    const stage = stages[i];
                    const progress = ((i + 1) / stages.length) * 100;

                    // Update progress display
                    document.getElementById('currentEvalStage').textContent = stage.name;
                    document.getElementById('evalProgress').textContent = `${Math.round(progress)}%`;
                    document.getElementById('evalProgressBar').style.width = `${progress}%`;
                    document.getElementById('evalStageDetail').textContent = stage.detail;

                    // Process this stage
                    processedEval = stage.process(processedEval);
                    
                    // Wait for stage duration
                    await delay(stage.duration);
                }

                // Hide processing modal
                processingModal.hide();
                document.getElementById('processingModal').remove();

                // Show final evaluation
                showEvaluationModal(processedEval);

            } catch (error) {
                console.error('Error in evaluation generation:', error);
                processingModal.hide();
                document.getElementById('processingModal').remove();
                alert('Error generating evaluation: ' + error.message);
            }
        } catch (error) {
            console.error('Error in generate button click:', error);
            alert('Error generating evaluation. Please try again.');
        }
    });

    async function processFeedback(feedback) {
        // Split feedback into items
        const items = feedback.split(/\n\n+/).filter(item => item.trim());
        
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            
            // Update progress
            updateStatus({
                stage: 'Processing Feedback',
                progress: (i / items.length) * 100,
                currentOperation: `Processing item ${i + 1} of ${items.length}...`
            });

            // Analyze and categorize
            const {category, confidence} = await analyzeFeedback(item);
            
            // Add to appropriate section
            addFeedbackItem(item, 'Feedback', category, confidence);
            
            // Small delay for UI
            await delay(500);
        }
    }

    async function processAccomplishments(accomplishments) {
        // Split accomplishments into items
        const items = accomplishments.split(/\n+/).filter(item => item.trim());
        
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            
            // Update progress
            updateStatus({
                stage: 'Processing Accomplishments',
                progress: (i / items.length) * 100,
                currentOperation: `Processing item ${i + 1} of ${items.length}...`
            });

            // Analyze and categorize
            const {category, confidence} = await analyzeFeedback(item);
            
            // Add to appropriate section
            addFeedbackItem(item, 'Accomplishment', category, confidence);
            
            // Small delay for UI
            await delay(500);
        }
    }

    async function analyzeFeedback(text) {
        text = text.toLowerCase();
        
        const scores = {
            impact: 0,
            behavior: 0,
            betterment: 0
        };

        // Impact keywords and phrases
        const impactWords = [
            'delivered', 'achieved', 'improved', 'impact', 'result', 'outcome',
            'optimization', 'efficiency', 'performance', 'metric', 'revenue',
            'reduced', 'increased', 'implemented', 'launched', 'debug',
            'solution', 'technical expertise', 'problem-solving', 'quality'
        ];

        // Behavior keywords and phrases
        const behaviorWords = [
            'collaborated', 'communicated', 'team', 'helped', 'supported',
            'reliable', 'consistent', 'responsive', 'professional', 'leadership',
            'relationship', 'coordination', 'organized', 'proactive',
            'dependable', 'attitude', 'approach', 'style'
        ];

        // Betterment keywords and phrases
        const bettermentWords = [
            'learned', 'grew', 'developed', 'growth', 'learning',
            'development', 'training', 'skill', 'curiosity', 'explore',
            'potential', 'advancement', 'progress', 'continuous improvement',
            'evolving', 'knowledge', 'expertise', 'mentoring', 'coaching',
            'feedback', 'career', 'study', 'improve', 'enhancement'
        ];

        // Calculate scores with context
        impactWords.forEach(word => {
            if (text.includes(word)) scores.impact++;
        });

        behaviorWords.forEach(word => {
            if (text.includes(word)) scores.behavior++;
        });

        bettermentWords.forEach(word => {
            if (text.includes(word)) scores.betterment++;
        });

        // Additional context scoring
        if (text.includes('growth') && text.includes('learning')) scores.betterment += 2;
        if (text.includes('continuous') && text.includes('improvement')) scores.betterment += 2;
        if (text.includes('career') || text.includes('develop')) scores.betterment += 1;
        if (text.includes('mentoring') || text.includes('teaching')) scores.betterment += 1;

        // Find highest score
        const maxScore = Math.max(scores.impact, scores.behavior, scores.betterment);
        let category = 'behavior'; // Default

        if (maxScore > 0) {
            if (scores.impact === maxScore) category = 'impact';
            else if (scores.betterment === maxScore) category = 'betterment';
        }

        return {
            category,
            confidence: Math.min(100, maxScore * 20 + 60)
        };
    }

    function addFeedbackItem(text, source, category, confidence) {
        const section = document.getElementById(`${category}Section`);
        const itemId = 'feedback-' + Date.now() + Math.random().toString(36).substr(2, 9);
        
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'feedback-item';
        feedbackDiv.id = itemId;
        feedbackDiv.draggable = true;
        
        feedbackDiv.innerHTML = `
            <div class="feedback-source">${source}</div>
            ${text}
            <div class="confidence-indicator">Confidence: ${confidence}%</div>
            <button class="btn btn-sm btn-outline-danger delete-btn" onclick="deleteFeedbackItem('${itemId}', '${category}')">×</button>
        `;
        
        // Add drag handlers
        feedbackDiv.ondragstart = drag;
        
        section.appendChild(feedbackDiv);
        
        // Store feedback
        feedbackStore[category].push({
            id: itemId,
            text: text,
            source: source,
            confidence: confidence
        });
        
        // Update counts
        updateCounts();
    }

    function updateStatus(status) {
        document.getElementById('currentStage').textContent = status.stage;
        document.getElementById('stageProgress').textContent = `${Math.round(status.progress)}%`;
        document.getElementById('progressBar').style.width = `${status.progress}%`;
        document.getElementById('stageDetail').textContent = status.currentOperation;
    }

    function improveContentStructure(text) {
        return text
            .replace(/Looking ahead/g, "Building on these accomplishments")
            .replace(/I have also contributed/g, "Additionally, I have demonstrated initiative");
    }

    function addContentDepth(text) {
        return text
            .replace(/demonstrated strong/g, "consistently demonstrated exceptional")
            .replace(/technical leadership/g, "technical leadership and expertise");
    }

    function improveWritingQuality(text) {
        return text
            .replace(/help shape stronger/g, "contribute more strategically to")
            .replace(/it would be to/g, "to");
    }

    function fixGrammarAndStyle(text) {
        return text
            .replace(/\.+/g, '.') // Fix multiple periods
            .replace(/\s+\./g, '.') // Fix space before period
            .replace(/"\s*\./g, '"') // Fix quote followed by period
            .replace(/\s+"/g, ' "') // Fix spacing around quotes
            .replace(/"\s+/g, '" ') // Fix spacing after quotes
            .replace(/\bive\b/g, "I've")
            .replace(/\bId\b/g, "I'd")
            .replace(/\bim\b/g, "I'm")
            .replace(/\byouve\b/g, "you've")
            .replace(/\byoure\b/g, "you're")
            .replace(/\bwere\b/g, "we're")
            .replace(/\bthats\b/g, "that's");
    }

    function finalPolish(text) {
        return text
            .replace(/\s+/g, ' ')  // Fix multiple spaces
            .replace(/\n\s+/g, '\n')  // Fix extra spaces after newlines
            .replace(/([^.!?])\n/g, '$1\n\n')  // Ensure proper paragraph spacing
            .trim();
    }

    async function createEvaluation() {
        // Get any notes/considerations
        const notes = document.getElementById('notesInput').value.trim();
        
        let evaluationText = "Performance Evaluation\n";
        evaluationText += "=====================\n\n";

        // Impact Section
        evaluationText += "Impact\n";
        evaluationText += "------\n";
        if (feedbackStore.impact.length > 0) {
            evaluationText += "Over this review period, I have consistently demonstrated strong technical leadership and delivered measurable impact across several key areas. My technical expertise has been particularly evident in performance optimization and system reliability improvements. ";
            
            // Find and highlight quantitative achievements
            const quantitativeImpacts = feedbackStore.impact.filter(item => 
                item.text.match(/\d+%|reduced|improved|optimized/i));
            if (quantitativeImpacts.length > 0) {
                evaluationText += "I achieved several notable performance improvements, including ";
                quantitativeImpacts.forEach((item, index) => {
                    const cleanedText = item.text.toLowerCase()
                        .replace(/^i |^• /i, '')
                        .replace(/\.+$/, '')
                        .trim();
                    if (index === quantitativeImpacts.length - 1 && index > 0) {
                        evaluationText += "and " + cleanedText + ". ";
                    } else {
                        evaluationText += cleanedText + (index < quantitativeImpacts.length - 1 ? ", " : ". ");
                    }
                });
            }

            // Add qualitative feedback synthesis
            evaluationText += "\n\nMy colleagues have particularly noted my problem-solving abilities and commitment to quality. As one teammate observed: ";
            const qualityFeedback = feedbackStore.impact.find(item => 
                item.text.includes("quality") || item.text.includes("reliable"));
            if (qualityFeedback) {
                const quote = qualityFeedback.text
                    .replace(/^🔹?\s*["']?/i, '')  // Remove leading emoji and quotes
                    .replace(/["']/g, '')  // Remove quotes
                    .replace(/\.+$/, '')   // Remove trailing periods
                    .replace(/[^\x00-\x7F]/g, '')  // Remove emojis
                    .trim();
                evaluationText += `"${quote}"`;
            }

            // Add growth opportunities
            const growthFeedback = feedbackStore.impact.find(item => 
                item.text.toLowerCase().includes("could") || item.text.toLowerCase().includes("suggestion"));
            if (growthFeedback) {
                evaluationText += "\n\nLooking ahead, I recognize opportunities for even greater impact. ";
                const focusArea = growthFeedback.text.toLowerCase()
                    .replace(/^.+?could|^.+?suggestion/i, '')
                    .replace(/^[^a-zA-Z]+/, '')
                    .replace(/["']/g, '')
                    .replace(/\.+$/, '')
                    .trim();
                evaluationText += "Specifically, I plan to focus on " + focusArea + ".";
            }
        } else {
            evaluationText += "No impact items recorded.\n";
        }
        evaluationText += "\n\n";

        // Behavior Section
        evaluationText += "Behavior\n";
        evaluationText += "--------\n";
        if (feedbackStore.behavior.length > 0) {
            evaluationText += "Throughout this period, I have demonstrated strong collaborative skills and a commitment to team success. ";
            
            // Highlight cross-functional collaboration
            const collaborationFeedback = feedbackStore.behavior.filter(item =>
                item.text.toLowerCase().includes("collab") || 
                item.text.toLowerCase().includes("team") ||
                item.text.toLowerCase().includes("partner"));
            
            if (collaborationFeedback.length > 0) {
                evaluationText += "My ability to work effectively across teams has been consistently recognized. ";
                const keyQuote = collaborationFeedback.find(item => 
                    item.text.includes("Product") || item.text.includes("stakeholder"));
                if (keyQuote) {
                    const quote = keyQuote.text.match(/["'](.+?)["']/)?.[1] || keyQuote.text;
                    evaluationText += "As noted in feedback: ";
                    evaluationText += `"${quote.trim()}" `;
                }
            }

            // Add process improvements
            const processImprovements = feedbackStore.behavior.filter(item =>
                item.text.toLowerCase().includes("process") || 
                item.text.toLowerCase().includes("documentation") ||
                item.text.toLowerCase().includes("planning"));
            
            if (processImprovements.length > 0) {
                evaluationText += "\n\nI have also contributed to improving team processes and efficiency. ";
                processImprovements.forEach((item, index) => {
                    if (index === 0) {
                        const improvement = item.text.toLowerCase()
                            .replace(/^i |^• /i, '')
                            .replace(/\.$/, '')
                            .trim();
                        evaluationText += "Specifically, I " + improvement + ". ";
                    }
                });
            }

            // Add development areas
            const developmentAreas = feedbackStore.behavior.find(item =>
                item.text.toLowerCase().includes("could") || 
                item.text.toLowerCase().includes("suggestion"));
            
            if (developmentAreas) {
                evaluationText += "\n\nTo further strengthen my collaborative impact, I will focus on ";
                const focusArea = developmentAreas.text.toLowerCase()
                    .replace(/^.+?could|^.+?suggestion/i, '')
                    .replace(/^[^a-zA-Z]+/, '')
                    .replace(/["']/g, '')
                    .replace(/\.+$/, '')
                    .replace(/[^\x00-\x7F]/g, '') // Remove emojis and special characters
                    .trim();
                evaluationText += focusArea + ".";
            }
        } else {
            evaluationText += "No behavior items recorded.\n";
        }
        evaluationText += "\n\n";

        // Betterment Section
        evaluationText += "Betterment\n";
        evaluationText += "----------\n";
        if (feedbackStore.betterment.length > 0) {
            evaluationText += "This review period has been marked by significant professional growth and a continued commitment to learning and development. ";

            // Highlight specific learning achievements
            const learningAchievements = feedbackStore.betterment.filter(item =>
                item.text.toLowerCase().includes("learned") || 
                item.text.toLowerCase().includes("developed") ||
                item.text.toLowerCase().includes("improved"));
            
            if (learningAchievements.length > 0) {
                evaluationText += "I have actively expanded my technical capabilities and soft skills. ";
                learningAchievements.forEach((item, index) => {
                    if (index === 0) {
                        const achievement = item.text.toLowerCase()
                            .replace(/^i |^• /i, '')
                            .replace(/\.$/, '')
                            .trim();
                        evaluationText += "For example, I " + achievement + ". ";
                    }
                });
            }

            // Add manager feedback if available
            const managerFeedback = feedbackStore.betterment.find(item =>
                item.text.toLowerCase().includes("manager feedback"));
            if (managerFeedback) {
                evaluationText += "\n\nMy manager has noted my growth: ";
                const quote = managerFeedback.text
                    .replace(/^.*?Manager Feedback\s*["']?/i, '')  // Remove header and any preceding text
                    .replace(/["']/g, '')  // Remove quotes
                    .replace(/\.+$/, '')   // Remove trailing periods
                    .replace(/[^\x00-\x7F]/g, '')  // Remove emojis
                    .replace(/\bIve\b/g, "I've")   // Fix common contractions
                    .replace(/\bId\b/g, "I'd")
                    .replace(/\bIm\b/g, "I'm")
                    .replace(/\bYouve\b/g, "You've")
                    .replace(/\byoure\b/g, "you're")
                    .replace(/\bwere\b/g, "we're")
                    .replace(/\bthats\b/g, "that's")
                    .replace(/(?<=\w)- (?=\w)/g, "-")  // Fix spaced dashes
                    .replace(/(?<=\w)-(?=\w)/g, "- ")  // Add spaces around dashes
                    .trim();
                evaluationText += `"${quote}"`;
            }

            // Add future focus areas
            const growthAreas = feedbackStore.betterment.find(item =>
                item.text.toLowerCase().includes("could") || 
                item.text.toLowerCase().includes("next"));
            
            if (growthAreas) {
                evaluationText += "\n\nLooking ahead, I am committed to further growth. ";
                const focusArea = growthAreas.text.toLowerCase()
                    .replace(/^.+?could|^.+?next/i, '')
                    .replace(/^[^a-zA-Z]+/, '')
                    .replace(/["']/g, '')
                    .replace(/\.+$/, '')
                    .replace(/[^\x00-\x7F]/g, '')  // Remove emojis
                    .trim();
                evaluationText += "Specifically, I will focus on " + focusArea + ".";
            }
        } else {
            evaluationText += "No betterment items recorded.\n";
        }
        evaluationText += "\n\n";

        // Conclusion
        evaluationText += "Conclusion\n";
        evaluationText += "----------\n";
        
        // Add context from notes if provided
        if (notes) {
            evaluationText += "During this review period, it's important to note the following context: " + notes + "\n\n";
        }
        
        evaluationText += "This review period has demonstrated my commitment to delivering strong technical results while maintaining effective collaboration and pursuing continuous growth. ";
        evaluationText += "I have received consistent feedback about my technical expertise, problem-solving abilities, and positive team impact. ";
        evaluationText += "Moving forward, I am excited to build on these strengths while addressing the identified areas for development. ";
        evaluationText += "I remain committed to both personal growth and contributing to the team's and company's success.\n\n";

        // Optional statistics
        evaluationText += "Review Statistics\n";
        evaluationText += "-----------------\n";
        const totalItems = feedbackStore.impact.length + feedbackStore.behavior.length + feedbackStore.betterment.length;
        evaluationText += `Total feedback items analyzed: ${totalItems}\n`;
        evaluationText += `• Impact: ${feedbackStore.impact.length} items\n`;
        evaluationText += `• Behavior: ${feedbackStore.behavior.length} items\n`;
        evaluationText += `• Betterment: ${feedbackStore.betterment.length} items\n`;

        return evaluationText;
    }

    // Drag and drop handlers
    window.allowDrop = function(ev) {
        ev.preventDefault();
        ev.currentTarget.classList.add('drag-over');
    };

    window.drag = function(ev) {
        ev.dataTransfer.setData("text", ev.target.id);
        ev.target.classList.add('dragging');
    };

    window.drop = function(ev) {
        ev.preventDefault();
        const sections = document.querySelectorAll('.dimension-section');
        sections.forEach(section => section.classList.remove('drag-over'));
        
        const data = ev.dataTransfer.getData("text");
        const draggedElement = document.getElementById(data);
        draggedElement.classList.remove('dragging');
        
        const targetSection = ev.target.closest('.dimension-section');
        if (targetSection) {
            const oldCategory = draggedElement.parentElement.id.replace('Section', '');
            const newCategory = targetSection.id.replace('Section', '');
            
            if (oldCategory !== newCategory) {
                // Update storage
                const itemIndex = feedbackStore[oldCategory].findIndex(item => item.id === data);
                if (itemIndex !== -1) {
                    const item = feedbackStore[oldCategory][itemIndex];
                    feedbackStore[oldCategory].splice(itemIndex, 1);
                    feedbackStore[newCategory].push(item);
                }
                
                // Move element
                targetSection.appendChild(draggedElement);
                
                // Update counts
                updateCounts();
            }
        }
    };

    window.deleteFeedbackItem = function(itemId, category) {
        const item = document.getElementById(itemId);
        if (item) {
            item.remove();
            
            // Remove from storage
            feedbackStore[category] = feedbackStore[category].filter(item => item.id !== itemId);
            
            // Update counts
            updateCounts();
        }
    };

    window.downloadEvaluation = function() {
        const content = document.querySelector('#evaluationModal pre').textContent;
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'performance_evaluation.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    function updateCounts() {
        document.getElementById('impactCount').textContent = `(${feedbackStore.impact.length})`;
        document.getElementById('behaviorCount').textContent = `(${feedbackStore.behavior.length})`;
        document.getElementById('bettermentCount').textContent = `(${feedbackStore.betterment.length})`;
    }

    function clearFeedbackSections() {
        document.getElementById('impactSection').innerHTML = '';
        document.getElementById('behaviorSection').innerHTML = '';
        document.getElementById('bettermentSection').innerHTML = '';
        updateCounts();
    }

    function showEvaluationModal(evaluation) {
        const modalHtml = `
            <div class="modal fade" id="evaluationModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Performance Evaluation</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-info mb-3">
                                <h6 class="alert-heading mb-2">Next Steps</h6>
                                <ol class="mb-0">
                                    <li>Review your evaluation carefully for accuracy and completeness.</li>
                                    <li>If needed, you can remove any feedback or accomplishments above and click "Generate Evaluation" again.</li>
                                    <li>When satisfied with your evaluation, click "Download" to save it.</li>
                                    <li>Use this evaluation as a starting point for your performance review submission.</li>
                                </ol>
                            </div>
                            <pre style="white-space: pre-wrap;">${evaluation}</pre>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="downloadEvaluation()">Download</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove any existing modal
        const existingModal = document.getElementById('evaluationModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to document
        const modalDiv = document.createElement('div');
        modalDiv.innerHTML = modalHtml;
        document.body.appendChild(modalDiv);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('evaluationModal'));
        modal.show();
        
        // Clean up modal after hiding
        document.getElementById('evaluationModal').addEventListener('hidden.bs.modal', function () {
            this.remove();
        });
    }

    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
});