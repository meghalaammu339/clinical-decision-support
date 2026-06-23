import { useState } from "react";
import "./Followupchat.css";

export default function FollowUpChat({ report }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!question.trim()) return;
    const userMsg = { role: "user", text: question };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/followup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMsg.text, report }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "ai", text: data.answer }]);
    } catch {
      setMessages((prev) => [...prev, { role: "ai", text: "Sorry, something went wrong." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter") handleAsk();
  };

  return (
    <div className="followup-section">
      <h3>🤖 Ask About This Report</h3>
      <p className="followup-hint">Ask anything about the diagnosis, tests, or next steps</p>

      {messages.length > 0 && (
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              <span className="chat-icon">{msg.role === "user" ? "👤" : "🤖"}</span>
              <p>{msg.text}</p>
            </div>
          ))}
          {loading && (
            <div className="chat-msg ai">
              <span className="chat-icon">🤖</span>
              <p className="typing">Thinking...</p>
            </div>
          )}
        </div>
      )}

      <div className="chat-input">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKey}
          placeholder="e.g. What does troponin test involve?"
          disabled={loading}
        />
        <button onClick={handleAsk} disabled={loading || !question.trim()}>
          Ask →
        </button>
      </div>
    </div>
  );
}