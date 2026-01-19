let recognition;
const core = document.getElementById("core");
const statusText = document.getElementById("status");
const waves = document.getElementById("waves");

function startVoice() {

    // 🔴 CHECK BROWSER SUPPORT
    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert("Speech Recognition not supported in this browser. Please use Google Chrome on desktop.");
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = false;

    core.classList.add("listening");
    statusText.innerText = "Listening...";
    waves.classList.remove("hidden");

    recognition.onresult = function (event) {
        const text = event.results[0][0].transcript;

        document.getElementById("cmd").innerText = text;

        fetch("/voice/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({ text })
        })
        .then(res => res.json())
        .then(data => {
            core.classList.remove("listening");
            waves.classList.add("hidden");
            speak(data.response);
        })
        .catch(() => {
            statusText.innerText = "Server error";
        });
    };

    recognition.onerror = function (event) {
        console.error("Speech error:", event.error);
        core.classList.remove("listening");
        waves.classList.add("hidden");
        statusText.innerText = "Mic error. Try again.";
    };

    recognition.onend = function () {
        core.classList.remove("listening");
        waves.classList.add("hidden");
        statusText.innerText = "Tap the core to speak";
    };

    recognition.start();
}

function speak(text) {
    const msg = new SpeechSynthesisUtterance(text);
    msg.lang = "en-IN";

    core.classList.add("speaking");
    statusText.innerText = "Speaking...";
    waves.classList.remove("hidden");

    msg.onend = () => {
        core.classList.remove("speaking");
        waves.classList.add("hidden");
        statusText.innerText = "Tap the core to speak";
    };

    document.getElementById("res").innerText = text;
    window.speechSynthesis.speak(msg);
}

// CSRF helper (required on Render)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
