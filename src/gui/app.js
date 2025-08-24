class KompanApp {
    constructor() {
        this.config = {
            scanningInterval: 2000, // 2 seconds
            currentlyHighlighted: 'yes', // 'yes' or 'no'
            isScanning: false,
            isTTSSpeaking: false,
            isPaused: false,
            conversationEnded: false,
            reconnectAttempts: 0,
            maxReconnectAttempts: 5
        };
        
        this.elements = {
            yesBtn: document.getElementById('yes-btn'),
            noBtn: document.getElementById('no-btn'),
            questionText: document.getElementById('question-text'),
            status: document.getElementById('status'),
            pauseBtn: document.getElementById('pause-btn'),
            restartBtn: document.getElementById('restart-btn'),
            settingsBtn: document.getElementById('settings-btn'),
            settingsPanel: document.getElementById('settings-panel'),
            closeSettings: document.getElementById('close-settings'),
            scanSpeed: document.getElementById('scan-speed'),
            scanSpeedValue: document.getElementById('scan-speed-value'),
            ttsEngine: document.getElementById('tts-engine'),
            debugPanel: document.getElementById('debug-panel'),
            debugInfo: document.getElementById('debug-info')
        };
        
        this.scanTimer = null;
        this.websocket = null;
        
        this.init();
    }
    
    async init() {
        this.updateStatus('Ładowanie...', 'loading');
        
        // Initialize WebSocket connection
        await this.connectWebSocket();
        
        // Bind events
        this.bindEvents();
        
        // Load settings
        await this.loadSettings();
        
        // Initialize TTS
        await this.initializeTTS();
        
        this.updateStatus('Gotowy', 'ready');
        
        // Start initial conversation
        this.startConversation();
    }
    
    async connectWebSocket() {
        try {
            const wsUrl = `ws://${window.location.hostname}:${window.location.port}/ws`;
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.debug('WebSocket połączony');
                this.config.reconnectAttempts = 0; // Reset reconnect attempts
                this.updateStatus('Połączony', 'ready');
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.debug('WebSocket rozłączony - próba ponownego połączenia');
                this.updateStatus('Połączenie przerwane - łączenie...', 'error');
                
                // Try to reconnect with exponential backoff
                this.config.reconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, this.config.reconnectAttempts), 10000);
                
                setTimeout(() => {
                    if (this.config.reconnectAttempts <= this.config.maxReconnectAttempts) {
                        this.connectWebSocket();
                    } else {
                        this.updateStatus('Błąd połączenia - kliknij aby kontynuować', 'error');
                        this.enableEmergencyMode();
                    }
                }, delay);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.debug(`WebSocket błąd: ${error}`);
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'question':
                this.displayQuestion(data.text);
                break;
            case 'tts_start':
                this.onTTSStart();
                break;
            case 'tts_end':
                this.onTTSEnd();
                break;
            case 'conversation_end':
                this.onConversationEnd(data.summary);
                break;
            case 'status':
                this.updateStatus(data.message, data.level);
                break;
            case 'debug':
                this.debug(data.message);
                break;
        }
    }
    
    bindEvents() {
        // Response buttons (left click only)
        document.addEventListener('click', (e) => {
            if (e.button === 0) { // Left click only
                this.handleClick();
            }
        });
        
        // Control buttons
        this.elements.pauseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.togglePause();
        });
        
        this.elements.restartBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.restartConversation();
        });
        
        this.elements.settingsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showSettings();
        });
        
        this.elements.closeSettings.addEventListener('click', () => {
            this.hideSettings();
        });
        
        // Settings controls
        this.elements.scanSpeed.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            this.config.scanningInterval = value * 1000;
            this.elements.scanSpeedValue.textContent = `${value}s`;
            this.saveSettings();
        });
        
        this.elements.ttsEngine.addEventListener('change', () => {
            this.saveSettings();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' || e.code === 'Enter') {
                e.preventDefault();
                this.handleClick();
            } else if (e.code === 'KeyP') {
                this.togglePause();
            } else if (e.code === 'KeyR') {
                this.restartConversation();
            }
        });
    }
    
    handleClick() {
        // Emergency recovery - if user clicks and system is stuck, restart scanning
        if (!this.config.isScanning && !this.config.isTTSSpeaking && !this.config.isPaused) {
            this.debug('Emergency recovery: restarting scanning');
            this.emergencyRestart();
            return;
        }
        
        if (this.config.isPaused || this.config.isTTSSpeaking || !this.config.isScanning) {
            return;
        }
        
        const selectedValue = this.config.currentlyHighlighted === 'yes';
        this.sendResponse(selectedValue);
    }
    
    async sendResponse(isYes) {
        this.stopScanning();
        
        // Visual feedback
        const selectedBtn = isYes ? this.elements.yesBtn : this.elements.noBtn;
        selectedBtn.classList.add('scanning');
        
        let responseSuccess = false;
        
        // Try WebSocket first
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            try {
                this.websocket.send(JSON.stringify({
                    type: 'response',
                    value: isYes
                }));
                responseSuccess = true;
            } catch (error) {
                console.error('WebSocket send failed:', error);
            }
        }
        
        // Fallback to HTTP if WebSocket failed
        if (!responseSuccess) {
            try {
                const response = await fetch('/api/respond', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ response: isYes })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    responseSuccess = true;
                    
                    // Handle response directly if WebSocket is down
                    if (data.question) {
                        this.displayQuestion(data.question);
                        
                        // Try to speak the question
                        try {
                            await fetch('/api/tts/speak', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ text: data.question })
                            });
                            // Wait for TTS to finish
                            setTimeout(() => {
                                this.startScanning();
                            }, 3000);
                        } catch (ttsError) {
                            console.error('TTS failed for response:', ttsError);
                            // Start scanning anyway after shorter delay
                            setTimeout(() => {
                                this.startScanning();
                            }, 1000);
                        }
                    } else {
                        // Conversation ended
                        this.onConversationEnd('Rozmowa zakończona');
                    }
                }
            } catch (error) {
                console.error('HTTP fallback failed:', error);
                this.updateStatus('Błąd - kliknij aby spróbować ponownie', 'error');
                
                // Emergency recovery after 3 seconds
                setTimeout(() => {
                    this.emergencyRestart();
                }, 3000);
            }
        }
        
        // Remove visual feedback
        setTimeout(() => {
            selectedBtn.classList.remove('scanning');
        }, 500);
        
        this.debug(`Odpowiedź: ${isYes ? 'TAK' : 'NIE'} - Success: ${responseSuccess}`);
    }
    
    displayQuestion(text) {
        this.elements.questionText.textContent = text;
        this.debug(`Pytanie: ${text}`);
    }
    
    startScanning() {
        if (this.config.isPaused || this.config.isTTSSpeaking) {
            return;
        }
        
        this.config.isScanning = true;
        this.config.currentlyHighlighted = 'yes'; // Start with YES
        
        this.updateHighlight();
        
        // Play initial audio cue for first "TAK"
        this.playAudioCue();
        
        this.scanTimer = setInterval(() => {
            // Toggle between yes and no
            this.config.currentlyHighlighted = this.config.currentlyHighlighted === 'yes' ? 'no' : 'yes';
            this.updateHighlight();
            
            // Play audio cue
            this.playAudioCue();
        }, this.config.scanningInterval);
        
        this.debug('Skanowanie rozpoczęte');
    }
    
    stopScanning() {
        this.config.isScanning = false;
        
        if (this.scanTimer) {
            clearInterval(this.scanTimer);
            this.scanTimer = null;
        }
        
        // Remove all highlights
        this.elements.yesBtn.classList.remove('highlighted');
        this.elements.noBtn.classList.remove('highlighted');
        
        this.debug('Skanowanie zatrzymane');
    }
    
    updateHighlight() {
        // Remove existing highlights
        this.elements.yesBtn.classList.remove('highlighted');
        this.elements.noBtn.classList.remove('highlighted');
        
        // Add highlight to current button
        if (this.config.currentlyHighlighted === 'yes') {
            this.elements.yesBtn.classList.add('highlighted');
        } else {
            this.elements.noBtn.classList.add('highlighted');
        }
    }
    
    async playAudioCue() {
        const text = this.config.currentlyHighlighted === 'yes' ? 'tak' : 'nie';
        
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'audio_cue',
                text: text
            }));
        } else {
            // HTTP fallback for audio cues
            try {
                fetch('/api/tts/speak', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                }).catch(error => {
                    // Ignore audio cue errors - not critical
                    console.warn('Audio cue failed:', error);
                });
            } catch (error) {
                console.warn('Audio cue failed:', error);
            }
        }
    }
    
    onTTSStart() {
        this.config.isTTSSpeaking = true;
        this.stopScanning();
        document.body.classList.add('tts-speaking');
        this.updateStatus('Mówię...', 'loading');
    }
    
    onTTSEnd() {
        this.config.isTTSSpeaking = false;
        document.body.classList.remove('tts-speaking');
        this.updateStatus('Słucham...', 'ready');
        
        // Start scanning after TTS finishes
        setTimeout(() => {
            this.startScanning();
        }, 500);
    }
    
    togglePause() {
        this.config.isPaused = !this.config.isPaused;
        
        if (this.config.isPaused) {
            this.stopScanning();
            document.body.classList.add('conversation-paused');
            this.elements.pauseBtn.textContent = 'Wznów';
            this.updateStatus('Pauza', 'loading');
        } else {
            document.body.classList.remove('conversation-paused');
            this.elements.pauseBtn.textContent = 'Pauza';
            this.updateStatus('Gotowy', 'ready');
            
            if (!this.config.isTTSSpeaking) {
                this.startScanning();
            }
        }
    }
    
    async restartConversation() {
        this.stopScanning();
        this.config.isPaused = false;
        document.body.classList.remove('conversation-paused');
        this.elements.pauseBtn.textContent = 'Pauza';
        
        this.updateStatus('Restartowanie...', 'loading');
        
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({ type: 'restart' }));
        }
        
        this.startConversation();
    }
    
    async startConversation() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({ type: 'start_conversation' }));
        } else {
            // Fallback to direct question
            this.displayQuestion('Cześć! Jestem Twoim asystentem. Czy chciałbyś ze mną porozmawiać?');
            
            // Try to speak the question via HTTP API
            try {
                await fetch('/api/tts/speak', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: 'Cześć! Jestem Twoim asystentem. Czy chciałbyś ze mną porozmawiać?' })
                });
                // Wait a bit for TTS to finish, then start scanning
                setTimeout(() => this.onTTSEnd(), 3000);
            } catch (error) {
                console.error('TTS failed:', error);
                setTimeout(() => this.onTTSEnd(), 1000);
            }
        }
    }
    
    onConversationEnd(summary) {
        this.stopScanning();
        const endMessage = 'Dziękuję za rozmowę! Kliknij aby rozpocząć nową rozmowę.';
        this.displayQuestion(endMessage);
        this.debug(`Podsumowanie: ${summary}`);
        
        // Speak the end message
        try {
            fetch('/api/tts/speak', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: endMessage })
            }).catch(error => {
                console.warn('End message TTS failed:', error);
            });
        } catch (error) {
            console.warn('End message TTS failed:', error);
        }
        
        // After 5 seconds, enable emergency restart
        setTimeout(() => {
            this.config.conversationEnded = true;
        }, 5000);
    }
    
    showSettings() {
        this.elements.settingsPanel.classList.remove('hidden');
    }
    
    hideSettings() {
        this.elements.settingsPanel.classList.add('hidden');
    }
    
    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            const settings = await response.json();
            
            this.config.scanningInterval = settings.scanning_interval * 1000;
            this.elements.scanSpeed.value = settings.scanning_interval;
            this.elements.scanSpeedValue.textContent = `${settings.scanning_interval}s`;
            this.elements.ttsEngine.value = settings.tts_engine;
            
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }
    
    async saveSettings() {
        const settings = {
            scanning_interval: this.config.scanningInterval / 1000,
            tts_engine: this.elements.ttsEngine.value
        };
        
        try {
            await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
        } catch (error) {
            console.error('Failed to save settings:', error);
        }
    }
    
    async initializeTTS() {
        try {
            const response = await fetch('/api/tts/initialize', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.debug(`TTS zainicjalizowany: ${result.engine}`);
            } else {
                this.debug('Błąd inicjalizacji TTS');
                this.updateStatus('Błąd TTS', 'error');
            }
        } catch (error) {
            console.error('TTS initialization failed:', error);
            this.debug('Błąd połączenia z TTS');
        }
    }
    
    updateStatus(message, level = 'ready') {
        this.elements.status.textContent = message;
        
        // Remove all status classes
        document.body.classList.remove('loading', 'ready', 'error');
        // Add current status class
        document.body.classList.add(level);
    }
    
    debug(message) {
        console.log(message);
        
        const timestamp = new Date().toLocaleTimeString();
        this.elements.debugInfo.innerHTML += `<div>${timestamp}: ${message}</div>`;
        
        // Keep only last 10 debug messages
        const debugLines = this.elements.debugInfo.children;
        if (debugLines.length > 10) {
            debugLines[0].remove();
        }
        
        // Show debug panel if there are messages
        if (debugLines.length > 0) {
            this.elements.debugPanel.style.display = 'block';
        }
    }
    
    emergencyRestart() {
        this.debug('EMERGENCY RESTART - przywracanie działania');
        
        // Reset all states
        this.config.isPaused = false;
        this.config.isTTSSpeaking = false;
        this.config.isScanning = false;
        this.config.conversationEnded = false;
        this.config.emergencyMode = false;
        
        // Clear any timers
        if (this.scanTimer) {
            clearInterval(this.scanTimer);
            this.scanTimer = null;
        }
        
        // Remove all visual states
        document.body.classList.remove('tts-speaking', 'conversation-paused', 'emergency-mode');
        this.elements.yesBtn.classList.remove('highlighted', 'scanning');
        this.elements.noBtn.classList.remove('highlighted', 'scanning');
        this.elements.pauseBtn.textContent = 'Pauza';
        
        // Try to reconnect WebSocket
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            this.connectWebSocket();
        }
        
        // Show recovery message and start new conversation
        this.displayQuestion('System przywrócony. Czy chciałbyś zacząć nową rozmowę?');
        this.updateStatus('Gotowy - kliknij aby odpowiedzieć', 'ready');
        
        // Start scanning after a short delay
        setTimeout(() => {
            this.startScanning();
        }, 1000);
    }
    
    enableEmergencyMode() {
        this.debug('Włączono tryb awaryjny');
        this.displayQuestion('Wystąpił problem z połączeniem. Kliknij w dowolnym miejscu aby spróbować ponownie.');
        this.updateStatus('Tryb awaryjny - kliknij aby kontynuować', 'error');
        
        // Enable click anywhere to restart
        this.config.emergencyMode = true;
        
        // Add visual emergency mode styling
        document.body.classList.add('emergency-mode');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new KompanApp();
});