// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize particles background
    if (typeof particlesJS !== 'undefined') {
        particlesJS('particles-js', {
            particles: {
                number: { value: 80, density: { enable: true, value_area: 800 } },
                color: { value: "#8b5cf6" },
                shape: { type: "circle" },
                opacity: { value: 0.5, random: true },
                size: { value: 3, random: true },
                line_linked: {
                    enable: true,
                    distance: 150,
                    color: "#6366f1",
                    opacity: 0.2,
                    width: 1
                },
                move: {
                    enable: true,
                    speed: 2,
                    direction: "none",
                    random: true,
                    straight: false,
                    out_mode: "out",
                    bounce: false
                }
            },
            interactivity: {
                detect_on: "canvas",
                events: {
                    onhover: { enable: true, mode: "repulse" },
                    onclick: { enable: true, mode: "push" }
                }
            }
        });
    }

    // Initialize typing animation
    const typingText = document.querySelector('.typing-text');
    const texts = [
        "Real-time AI Sign Language Translation",
        "Breaking Communication Barriers",
        "Multilingual Gesture Recognition",
        "Powered by Advanced Computer Vision"
    ];
    
    let textIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    
    function typeEffect() {
        const currentText = texts[textIndex];
        
        if (isDeleting) {
            typingText.textContent = currentText.substring(0, charIndex - 1);
            charIndex--;
        } else {
            typingText.textContent = currentText.substring(0, charIndex + 1);
            charIndex++;
        }
        
        if (!isDeleting && charIndex === currentText.length) {
            isDeleting = true;
            setTimeout(typeEffect, 2000);
        } else if (isDeleting && charIndex === 0) {
            isDeleting = false;
            textIndex = (textIndex + 1) % texts.length;
            setTimeout(typeEffect, 500);
        } else {
            setTimeout(typeEffect, isDeleting ? 50 : 100);
        }
    }
    
    setTimeout(typeEffect, 1000);

    // DOM Elements
    const statusPulse = document.getElementById('statusPulse');
    const statusText = document.getElementById('statusText');
    const statusDetail = document.getElementById('statusDetail');
    const videoFeed = document.getElementById('videoFeed');
    const langSelect = document.getElementById('langSelect');
    const historyList = document.getElementById('historyList');
    const enText = document.getElementById('enText');
    const taText = document.getElementById('taText');
    const hiText = document.getElementById('hiText');
    const enOutput = document.getElementById('enOutput');
    const taOutput = document.getElementById('taOutput');
    const hiOutput = document.getElementById('hiOutput');
    const translationMode = document.getElementById('translationMode');
    const helpBtn = document.getElementById('helpBtn');
    const helpModal = document.getElementById('helpModal');
    const closeHelpModal = document.getElementById('closeHelpModal');
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    const copyAllBtn = document.getElementById('copyAllBtn');
    const speakBtn = document.getElementById('speakBtn');
    const clearBtn = document.getElementById('clearBtn');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    const toggleHistory = document.getElementById('toggleHistory');
    const handConfidence = document.getElementById('handConfidence');
    const frameRate = document.getElementById('frameRate');
    const currentGestureHint = document.getElementById('currentGestureHint');
    const detectedGestures = document.getElementById('detectedGestures');
    const totalSigns = document.getElementById('totalSigns');
    const lastSignTime = document.getElementById('lastSignTime');

    // Variables
    let lastData = null;
    let frameCount = 0;
    let lastFrameTime = Date.now();
    let gestureCount = 0;
    let historyItems = [];
    let currentLanguage = 'all';

    // Initialize stats
    updateStats();

    // Event Listeners
    langSelect.addEventListener('change', function() {
        currentLanguage = this.value;
        const modeText = this.options[this.selectedIndex].text;
        translationMode.querySelector('.mode-badge').textContent = modeText;
        
        // Animate mode change
        translationMode.classList.add('animate__animated', 'animate__pulse');
        setTimeout(() => {
            translationMode.classList.remove('animate__animated', 'animate__pulse');
        }, 500);
        
        // Update language visibility
        updateLanguageVisibility();
        
        // Send to server
        fetch("/set_language", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: "lang=" + this.value
        });
    });

    helpBtn.addEventListener('click', () => {
        helpModal.style.display = 'flex';
    });

    closeHelpModal.addEventListener('click', () => {
        helpModal.style.display = 'none';
    });

    helpModal.addEventListener('click', (e) => {
        if (e.target === helpModal) {
            helpModal.style.display = 'none';
        }
    });

    fullscreenBtn.addEventListener('click', toggleFullscreen);

    copyAllBtn.addEventListener('click', copyAllTranslations);

    speakBtn.addEventListener('click', speakTranslations);

    clearBtn.addEventListener('click', clearTranslations);

    clearHistoryBtn.addEventListener('click', clearHistory);

    toggleHistory.addEventListener('click', () => {
        const historyCard = document.querySelector('.history-card');
        historyCard.style.display = historyCard.style.display === 'none' ? 'block' : 'none';
        
        // Show toast notification
        Toastify({
            text: historyCard.style.display === 'none' ? "History hidden" : "History shown",
            duration: 2000,
            gravity: "bottom",
            position: "right",
            backgroundColor: historyCard.style.display === 'none' ? "#f59e0b" : "#10b981"
        }).showToast();
    });

    // Update FPS counter
    function updateFPS() {
        const now = Date.now();
        const delta = now - lastFrameTime;
        
        if (delta >= 1000) {
            const fps = Math.round((frameCount * 1000) / delta);
            frameRate.textContent = fps;
            frameCount = 0;
            lastFrameTime = now;
        }
        
        frameCount++;
        requestAnimationFrame(updateFPS);
    }

    updateFPS();

    // Main data fetching loop
    setInterval(() => {
        fetch('/get_data')
        .then(res => res.json())
        .then(data => {
            // Update status
            updateStatus(data.status);
            
            // Update translations
            updateTranslations(data);
            
            // Update history
            updateHistory(data.history);
            
            // Update stats
            updateStats(data);
            
            // Store last data
            lastData = data;
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            updateStatus('Error connecting to server');
        });
    }, 400);

    // Functions
    function updateStatus(status) {
        const isConnected = status === 'Hand Detected';
        
        statusPulse.className = isConnected ? 'status-pulse connected' : 'status-pulse';
        statusText.textContent = isConnected ? 'Hand Detected - Active' : 'Waiting for hand...';
        statusDetail.textContent = isConnected ? 'Processing gestures in real-time' : 'Show your hand to the camera';
        
        if (isConnected) {
            statusText.classList.add('animate__animated', 'animate__pulse');
            setTimeout(() => {
                statusText.classList.remove('animate__animated', 'animate__pulse');
            }, 1000);
        }
    }

    function updateTranslations(data) {
        const lang = data.lang || currentLanguage;
        
        // Update text with animation if changed
        if (data.text.en !== enText.textContent && data.text.en) {
            animateTextChange(enText, data.text.en);
            updateConfidence('en', Math.random() * 30 + 70); // Simulated confidence
            gestureCount++;
        }
        
        if (data.text.ta !== taText.textContent && data.text.ta) {
            animateTextChange(taText, data.text.ta);
            updateConfidence('ta', Math.random() * 30 + 70);
        }
        
        if (data.text.hi !== hiText.textContent && data.text.hi) {
            animateTextChange(hiText, data.text.hi);
            updateConfidence('hi', Math.random() * 30 + 70);
        }
        
        // Update language visibility
        updateLanguageVisibility();
        
        // Update gesture hint
        if (data.text.en && data.text.en !== '---') {
            updateGestureHint(data.text.en);
        }
    }

    function animateTextChange(element, newText) {
        element.classList.remove('animate-text');
        void element.offsetWidth; // Trigger reflow
        element.textContent = newText;
        element.classList.add('animate-text');
    }

    function updateConfidence(lang, confidence) {
        const bar = document.getElementById(`${lang}Confidence`);
        const text = document.getElementById(`${lang}ConfidenceText`);
        
        if (bar && text) {
            bar.style.width = `${confidence}%`;
            text.textContent = `${Math.round(confidence)}%`;
            
            // Update hand confidence
            handConfidence.textContent = `${Math.round(confidence)}%`;
            
            // Update output card state
            const outputCard = document.getElementById(`${lang}Output`);
            outputCard.classList.add('active');
            setTimeout(() => {
                outputCard.classList.remove('active');
            }, 1000);
        }
    }

    function updateLanguageVisibility() {
        const showEn = currentLanguage === 'en' || currentLanguage === 'all';
        const showTa = currentLanguage === 'ta' || currentLanguage === 'all';
        const showHi = currentLanguage === 'hi' || currentLanguage === 'all';
        
        enOutput.style.display = showEn ? 'block' : 'none';
        taOutput.style.display = showTa ? 'block' : 'none';
        hiOutput.style.display = showHi ? 'block' : 'none';
    }

    function updateHistory(history) {
        if (!history || history.length === 0) return;
        
        // Clear empty state if it exists
        const emptyState = historyList.querySelector('.history-empty');
        if (emptyState) emptyState.remove();
        
        // Add new history items
        history.forEach((item, index) => {
            if (!historyItems.includes(item)) {
                addHistoryItem(item);
                historyItems.unshift(item);
                if (historyItems.length > 5) historyItems.pop();
            }
        });
        
        totalSigns.textContent = historyItems.length;
    }

    function addHistoryItem(text) {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.innerHTML = `
            <div class="history-item-header">
                <span class="history-item-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                <span class="history-item-confidence">${Math.round(Math.random() * 20 + 80)}%</span>
            </div>
            <div class="history-item-content">${text}</div>
            <div class="history-item-languages">
                <span>🇺🇸 English</span>
                <span>🇮🇳 Tamil</span>
                <span>🇮🇳 Hindi</span>
            </div>
        `;
        
        historyList.insertBefore(historyItem, historyList.firstChild);
        
        // Limit to 5 items
        const items = historyList.querySelectorAll('.history-item');
        if (items.length > 5) {
            items[items.length - 1].remove();
        }
        
        // Update last sign time
        lastSignTime.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    function updateStats(data) {
        detectedGestures.textContent = gestureCount;
        
        // Simulate connection quality changes
        const qualities = ['Excellent', 'Good', 'Fair'];
        const randomQuality = qualities[Math.floor(Math.random() * qualities.length)];
        document.getElementById('connectionQuality').textContent = randomQuality;
        
        // Update response time
        if (data && data.responseTime) {
            document.getElementById('responseTime').textContent = data.responseTime;
        }
    }

    function updateGestureHint(gesture) {
        const hints = {
            'A': 'Great! Now try making a "B" sign',
            'B': 'Excellent! Try "C" next',
            'C': 'Perfect! How about "D"?',
            'D': 'Awesome! Try "E" now',
            'E': 'Well done! Continue with "F"'
        };
        
        currentGestureHint.textContent = hints[gesture] || `Try different signs to see more translations`;
    }

    function toggleFullscreen() {
        const elem = document.documentElement;
        
        if (!document.fullscreenElement) {
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.webkitRequestFullscreen) {
                elem.webkitRequestFullscreen();
            } else if (elem.msRequestFullscreen) {
                elem.msRequestFullscreen();
            }
            fullscreenBtn.innerHTML = '<i class="fas fa-compress"></i>';
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
        }
    }

    function copyAllTranslations() {
        const translations = [
            `English: ${enText.textContent}`,
            `Tamil: ${taText.textContent}`,
            `Hindi: ${hiText.textContent}`
        ].join('\n');
        
        navigator.clipboard.writeText(translations).then(() => {
            Toastify({
                text: "All translations copied to clipboard!",
                duration: 2000,
                gravity: "bottom",
                position: "right",
                backgroundColor: "#10b981"
            }).showToast();
        });
    }

    function speakTranslations() {
        if ('speechSynthesis' in window) {
            const speech = new SpeechSynthesisUtterance();
            speech.text = `${enText.textContent}. This means ${taText.textContent} in Tamil and ${hiText.textContent} in Hindi`;
            speech.lang = 'en-US';
            speech.rate = 1;
            speech.pitch = 1;
            speech.volume = 1;
            
            window.speechSynthesis.speak(speech);
            
            Toastify({
                text: "Speaking translations...",
                duration: 2000,
                gravity: "bottom",
                position: "right",
                backgroundColor: "#6366f1"
            }).showToast();
        } else {
            Toastify({
                text: "Speech synthesis not supported in your browser",
                duration: 3000,
                gravity: "bottom",
                position: "right",
                backgroundColor: "#ef4444"
            }).showToast();
        }
    }

    function clearTranslations() {
        enText.textContent = '---';
        taText.textContent = '---';
        hiText.textContent = '---';
        
        Toastify({
            text: "Translations cleared",
            duration: 2000,
            gravity: "bottom",
            position: "right",
            backgroundColor: "#f59e0b"
        }).showToast();
    }

    function clearHistory() {
        historyList.innerHTML = `
            <div class="history-empty">
                <i class="fas fa-history"></i>
                <p>No signs detected yet</p>
                <small>Make signs to see history here</small>
            </div>
        `;
        historyItems = [];
        totalSigns.textContent = '0';
        lastSignTime.textContent = '--:--';
        
        Toastify({
            text: "History cleared",
            duration: 2000,
            gravity: "bottom",
            position: "right",
            backgroundColor: "#ef4444"
        }).showToast();
    }

    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + H to toggle history
        if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
            e.preventDefault();
            toggleHistory.click();
        }
        
        // Ctrl/Cmd + F for fullscreen
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            toggleFullscreen();
        }
        
        // Esc to exit fullscreen or close modal
        if (e.key === 'Escape') {
            if (document.fullscreenElement) {
                toggleFullscreen();
            }
            if (helpModal.style.display === 'flex') {
                helpModal.style.display = 'none';
            }
        }
    });

    // Add hover effects to cards
    const cards = document.querySelectorAll('.glass-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-5px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Initialize with a welcome toast
    setTimeout(() => {
        Toastify({
            text: "Welcome to GestureAI! Show your hand to begin translating.",
            duration: 4000,
            gravity: "top",
            position: "center",
            backgroundColor: "linear-gradient(135deg, #6366f1, #8b5cf6)"
        }).showToast();
    }, 1000);
});