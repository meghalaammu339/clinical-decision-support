import { useState } from "react";
import "./VoiceInput.css";

export default function VoiceInput({ onTranscript }) {
  const [listening, setListening] = useState(false);
  const supported = "webkitSpeechRecognition" in window || "SpeechRecognition" in window;

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      onTranscript(transcript);
    };
    recognition.onerror = () => setListening(false);
    recognition.start();
  };

  if (!supported) return null;

  return (
    <button
      type="button"
      className={`voice-btn ${listening ? "listening" : ""}`}
      onClick={startListening}
      disabled={listening}
    >
      {listening ? "🔴 Listening..." : "🎤 Speak"}
    </button>
  );
}