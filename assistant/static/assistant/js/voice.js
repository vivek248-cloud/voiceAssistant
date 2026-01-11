// UI elements
const core = document.getElementById("core");
const statusText = document.getElementById("status");
const cmdBox = document.getElementById("cmd");
const resBox = document.getElementById("res");
let recognition = null;
let isSpeaking = false;

// Start voice recognition
function startVoice() {
    // Browser support check
    if (!("webkitSpeechRecognition" in window)) {
        alert("Speech Recognition not supported in this browser. Use Chrome or Edge.");
        return;
    }

    recognition = new webkitSpeechRecognition();

    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    // UI: listening state
    core.classList.add("listening");
    statusText.innerText = "Listening...";

    recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        cmdBox.innerText = text;

        fetch("/voice/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text: text })
        })
        .then(res => res.json())
        .then(data => {
            core.classList.remove("listening");

            // 🔑 BACKEND RETURNS: { action, text, url }
            if (data.action === "open") {
                // Open YouTube / Spotify / Google
                window.open(data.url, "_blank");
                speak(data.text);
            } 
            else if (data.action === "speak") {
                speak(data.text);
            } 
            else {
                speak("Sorry, something went wrong.");
            }
        })
        .catch(err => {
            console.error(err);
            core.classList.remove("listening");
            statusText.innerText = "Error. Try again.";
        });
    };

    recognition.onerror = () => {
        core.classList.remove("listening");
        statusText.innerText = "Tap to try again";
    };

    recognition.start();
}

// Text-to-speech (Female Jarvis voice)
function speak(text) {
    if (!text) return;

    window.speechSynthesis.cancel(); // stop previous speech

    const msg = new SpeechSynthesisUtterance(text);
    msg.lang = "en-IN";
    msg.pitch = 1.2;
    msg.rate = 1;

    const voices = window.speechSynthesis.getVoices();
    msg.voice = voices.find(v =>
        v.name.toLowerCase().includes("female") ||
        v.name.toLowerCase().includes("zira") ||
        v.name.toLowerCase().includes("google")
    ) || voices[0];

    isSpeaking = true;
    core.classList.add("speaking");
    waves.classList.remove("hidden");
    statusText.innerText = "Speaking...";
    resBox.innerText = text;

    msg.onend = () => {
        isSpeaking = false;
        core.classList.remove("speaking");
        waves.classList.add("hidden");
        statusText.innerText = "Tap the core to speak";
    };

    window.speechSynthesis.speak(msg);
}

function stopAssistant() {
    // Stop speech
    window.speechSynthesis.cancel();
    isSpeaking = false;

    // Stop recognition
    if (recognition) {
        recognition.abort();
        recognition = null;
    }

    // Reset UI
    core.classList.remove("listening", "speaking");
    waves.classList.add("hidden");
    statusText.innerText = "Stopped. Tap to speak";
}

