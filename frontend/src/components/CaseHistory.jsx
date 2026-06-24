import "./CaseHistory.css";

const URGENCY_COLOR = {
  emergent: "#ef4444",
  urgent: "#f97316",
  routine: "#22c55e",
};

export default function CaseHistory({ history, onLoad, onClear }) {
  return (
    <div className="history-card">
      <div className="history-header">
        <h2>Case History</h2>
        <button className="btn-clear" onClick={onClear}>
          🗑 Clear All
        </button>
      </div>

      <div className="history-list">
        {history.map((item) => (
          <div key={item.id} className="history-item">
            <div className="history-info">
              <div className="history-top">
                <span
                  className="history-urgency"
                  style={{ background: URGENCY_COLOR[item.urgency] }}
                >
                  {item.urgency.toUpperCase()}
                </span>
                <span className="history-dx">{item.primary_diagnosis}</span>
              </div>
              <p className="history-symptoms">
                {((item.symptoms || item.result?.structured_case?.chief_complaint || "No details")).slice(0, 100)}
              </p>
              <p className="history-meta">
                {item.gender && `${item.gender} · `}{item.age && `${item.age} yrs · `}{item.timestamp}
              </p>
            </div>
            <button className="btn-load" onClick={() => onLoad(item)}>
              View →
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}