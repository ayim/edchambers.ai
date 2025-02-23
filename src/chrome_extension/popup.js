class AudioMonitor {
    constructor() {
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        this.isMonitoring = false;
        this.canvas = document.getElementById('visualizer');
        this.canvasCtx = this.canvas.getContext('2d');
        this.volumeLevel = document.getElementById('volumeLevel');
        this.transcriptionDiv = document.getElementById('transcription');
        
        this.startButton = document.getElementById('startButton');
        this.stopButton = document.getElementById('stopButton');
        
        this.startButton.addEventListener('click', () => this.startMonitoring());
        this.stopButton.addEventListener('click', () => this.stopMonitoring());
        
        this.recognition = null;
        this.setupSpeechRecognition();
        this.setupCanvas();
    }

    setupCanvas() {
        this.canvas.width = this.canvas.offsetWidth;
        this.canvas.height = this.canvas.offsetHeight;
    }

    setupSpeechRecognition() {
        if ('webkitSpeechRecognition' in window) {
            this.recognition = new webkitSpeechRecognition();
        } else if ('SpeechRecognition' in window) {
            this.recognition = new SpeechRecognition();
        } else {
            console.warn('Speech recognition not supported');
            return;
        }

        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript + ' ';
                } else {
                    interimTranscript += transcript;
                }
            }

            this.transcriptionDiv.innerHTML = 
                finalTranscript + 
                '<span class="interim">' + interimTranscript + '</span>';
            
            this.transcriptionDiv.scrollTop = this.transcriptionDiv.scrollHeight;
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
        };
    }

    async startMonitoring() {
        try {
            // Request microphone access through content script
            const response = await new Promise((resolve) => {
                chrome.runtime.sendMessage({type: 'GET_MICROPHONE'}, (response) => {
                    resolve(response);
                });
            });

            if (!response || !response.success) {
                throw new Error(response?.error || 'Failed to access microphone');
            }

            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            
            // Create a MediaStream from the audio track
            const audioTrack = response.stream.getAudioTracks()[0];
            const mediaStream = new MediaStream([audioTrack]);
            this.microphone = this.audioContext.createMediaStreamSource(mediaStream);
            
            this.analyser.fftSize = 2048;
            this.microphone.connect(this.analyser);
            
            this.isMonitoring = true;
            this.startButton.disabled = true;
            this.stopButton.disabled = false;
            
            if (this.recognition) {
                this.recognition.start();
            }
            
            this.draw();
        } catch (error) {
            console.error('Error accessing microphone:', error);
            let errorMessage = 'Error accessing microphone. ';
            
            if (error.message.includes('Permission')) {
                errorMessage += 'Please follow these steps to enable microphone access:\n' +
                              '1. Click the extension icon in the toolbar\n' +
                              '2. Click the three dots menu (...)\n' +
                              '3. Select "Manage extension"\n' +
                              '4. Scroll to "Site access"\n' +
                              '5. Under "Microphone", select "Allow"';
            } else {
                errorMessage += error.message;
            }
            
            alert(errorMessage);
            this.stopMonitoring();
        }
    }

    stopMonitoring() {
        if (this.audioContext) {
            this.microphone.disconnect();
            this.audioContext.close();
            this.isMonitoring = false;
            this.startButton.disabled = false;
            this.stopButton.disabled = true;
            
            if (this.recognition) {
                this.recognition.stop();
            }
        }
    }

    draw() {
        if (!this.isMonitoring) return;

        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        this.analyser.getByteTimeDomainData(dataArray);

        this.canvasCtx.fillStyle = '#f0f0f0';
        this.canvasCtx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.canvasCtx.lineWidth = 2;
        this.canvasCtx.strokeStyle = '#007bff';
        this.canvasCtx.beginPath();

        const sliceWidth = this.canvas.width * 1.0 / bufferLength;
        let x = 0;

        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i] / 128.0;
            sum += Math.abs(v - 1);
            const y = v * this.canvas.height / 2;

            if (i === 0) {
                this.canvasCtx.moveTo(x, y);
            } else {
                this.canvasCtx.lineTo(x, y);
            }

            x += sliceWidth;
        }

        this.canvasCtx.lineTo(this.canvas.width, this.canvas.height / 2);
        this.canvasCtx.stroke();

        const averageVolume = sum / bufferLength;
        const volumeDb = Math.round(20 * Math.log10(averageVolume) * 100) / 100;
        this.volumeLevel.textContent = `Volume Level: ${volumeDb} dB`;

        requestAnimationFrame(() => this.draw());
    }
}

// Initialize the audio monitor when the popup loads
document.addEventListener('DOMContentLoaded', () => {
    new AudioMonitor();
});
