let recognition;

function startVoice() {
    if (!("webkitSpeechRecognition" in window)) {
        alert("Speech Recognition is only supported in Google Chrome.");
        return;
    }

    recognition = new webkitSpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.continuous = false;

    const core = document.getElementById("core");
    const statusText = document.getElementById("status");

    core.classList.add("listening");
    statusText.innerText = "Listening...";

    recognition.onresult = function (event) {
        const text = event.results[0][0].transcript;
        document.getElementById("cmd").innerText = text;

        fetch("/voice/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        })
        .then(res => res.json())
        .then(data => {
            core.classList.remove("listening");
            speak(data.response);
        });
    };

    recognition.onerror = function (event) {
        core.classList.remove("listening");
        statusText.innerText = "Mic error. Tap to try again.";
        console.error(event.error);
    };

    recognition.onend = function () {
        core.classList.remove("listening");
    };

    recognition.start();
}

function speak(text) {
    const msg = new SpeechSynthesisUtterance(text);
    msg.lang = "en-IN";

    const core = document.getElementById("core");
    const statusText = document.getElementById("status");

    core.classList.add("speaking");
    statusText.innerText = "Speaking...";
    document.getElementById("res").innerText = text;

    msg.onend = () => {
        core.classList.remove("speaking");
        statusText.innerText = "Tap the core to speak";
    };

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(msg);
}
