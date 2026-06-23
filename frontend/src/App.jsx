import { useState, useEffect } from "react";
import { analyzePatientStream, approveCase } from "./services/api";
import PatientForm from "./components/PatientForm";
import DiagnosisReport from "./components/DiagnosisReport";
import PipelineTracker from "./components/PipelineTracker";
import CaseHistory from "./components/CaseHistory";
import ApprovalModal from "./components/ApprovalModal";
import "./App.css";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeNode, setActiveNode] = useState(null);
  const [streamData, setStreamData] = useState({});
  const [threadId, setThreadId] = useState(null);
  const [awaitingApproval, setAwaitingApproval] = useState(false);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const saved = localStorage.getItem("case_history");
    if (saved) setHistory(JSON.parse(saved));
  }, []);

  const saveToHistory = (formData, res) => {
    const newCase = {
      id: Date.now(),
      timestamp: new Date().toLocaleString(),
      symptoms: formData.symptoms,
      age: formData.age,
      gender: formData.gender,
      primary_diagnosis: res.final_report?.primary_diagnosis || "Unknown",
      urgency: res.final_report?.urgency || "routine",
      result: res,
    };
    const updated = [newCase, ...history].slice(0, 10);
    setHistory(updated);
    localStorage.setItem("case_history", JSON.stringify(updated));
  };

  const handleSubmit = (formData) => {
    setLoading(true);
    setResult(null);
    setError(null);
    setStreamData({});
    setActiveNode(null);

    analyzePatientStream(formData, {
      onThreadId: (id) => setThreadId(id),

      onNode: (event) => {
        setActiveNode(event.node);
        setStreamData((prev) => ({ ...prev, ...event.data, lastNode: event.node }));
      },

      onFinal: (data) => {
        setResult(data);
        const newCase = {
          id: Date.now(),
          timestamp: new Date().toLocaleString(),
          symptoms: formData.symptoms,
          age: formData.age,
          gender: formData.gender,
          primary_diagnosis: data.final_report?.primary_diagnosis || "Unknown",
          urgency: data.final_report?.urgency || "routine",
          result: data,
        };
        setHistory((h) => {
          const updated = [newCase, ...h].slice(0, 10);
          localStorage.setItem("case_history", JSON.stringify(updated));
          return updated;
        });
      },

      onAwaitingApproval: () => {
        setAwaitingApproval(true);
        setLoading(false);
      },

      onDone: () => {
        setLoading(false);
        setActiveNode(null);
      },

      onError: (msg) => {
        setError(typeof msg === "string" ? msg : "Something went wrong");
        setLoading(false);
        setActiveNode(null);
      },
    });
  };

  const handleApprove = async (approved, notes) => {
    setAwaitingApproval(false);
    setLoading(true);
    try {
      const data = await approveCase(threadId, approved, notes);
      if (data.status === "rejected") {
        setError("Case rejected by doctor.");
      } else {
        setResult(data);
        saveToHistory({}, data);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const loadCase = (caseItem) => {
    setResult(caseItem.result);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem("case_history");
  };

  const displayResult = result;

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">⚕️</span>
            <div>
              <h1>Clinical Decision Support</h1>
              <p>Agentic Multi-Agent AI System</p>
            </div>
          </div>
          <div className="badges">
            <span className="badge">LangGraph</span>
            <span className="badge">Guardrails</span>
            <span className="badge">HITL</span>
            <span className="badge">Streaming</span>
          </div>
        </div>
      </header>

      <main className="main">
        <PipelineTracker activeNode={activeNode} streamData={streamData} done={!!displayResult} />
        <PatientForm onSubmit={handleSubmit} loading={loading} />

        {error && <div className="error-box">⚠️ {error}</div>}

        {awaitingApproval && (
          <ApprovalModal
            diagnosis={streamData.primary_diagnosis}
            onDecide={handleApprove}
          />
        )}

        {displayResult && <DiagnosisReport data={displayResult} />}

        {history.length > 0 && (
          <CaseHistory history={history} onLoad={loadCase} onClear={clearHistory} />
        )}
      </main>

      <footer className="footer">
        LangGraph · Guardrails · Human-in-the-Loop · Streaming · FastAPI · React
      </footer>
    </div>
  );
}
