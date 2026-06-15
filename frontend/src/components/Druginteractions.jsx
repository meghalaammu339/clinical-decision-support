import { useState, useEffect } from "react";
import "./Druginteractions.css";

export default function DrugInteractions({ medications }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (medications && medications.length >= 2) {
      check();
    }
  }, []);

  const check = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/drug-interactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ medications }),
      });
      setResult(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!medications || medications.length < 2) return null;

  return (
    <div className="drug-section">
      <h3>💊 Drug Interaction Check</h3>
      <p className="drug-subtitle">Checked via OpenFDA Adverse Events Database</p>

      {loading && <p className="drug-loading">Checking interactions...</p>}

      {result && (
        result.interactions.length === 0 ? (
          <div className="drug-safe">✓ No significant interactions found</div>
        ) : (
          <div className="drug-list">
            {result.interactions.map((item, i) => (
              <div key={i} className={`drug-alert ${item.severity}`}>
                <div className="drug-alert-header">
                  <span className="drug-names">{item.drug1} + {item.drug2}</span>
                  <span className={`drug-sev ${item.severity}`}>{item.severity.toUpperCase()}</span>
                </div>
                <p>{item.message}</p>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  );
}