import { useState, useEffect } from "react";
import PatientForm from "./components/PatientForm";
import DiagnosisReport from "./components/DiagnosisReport";
import PipelineTracker from "./components/PipelineTracker";
import CaseHistory from "./components/CaseHistory";
import { analyzePatient } from "./services/api";
import "./App.css";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeStep, setActiveStep] = useState(null);
  const [history, setHistory] = useState([]);

  // Load history from localStorage on startup
  useEffect(() => {
    const saved = localStorage.getItem("case_history");
    if (saved) setHistory(JSON.parse(saved));
  }, []);

  const saveToHistory = (formData, result) => {
    const newCase = {
      id: Date.now(),
      timestamp: new Date().toLocaleString(),
      symptoms: formData.symptoms,
      age: formData.age,
      gender: formData.gender,
      primary_diagnosis: result.final_report?.primary_diagnosis || "Unknown",
      urgency: result.final_report?.urgency || "routine",
      result: result
    };

    const updated = [newCase, ...history].slice(0, 10); // keep last 10
    setHistory(updated);
    localStorage.setItem("case_history", JSON.stringify(updated));
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem("case_history");
  };

  const loadCase = (caseItem) => {
    setResult(caseItem.result);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleSubmit = async (formData) => {
    setLoading(true);
    setResult(null);
    setError(null);

    const steps = ["intake", "rag", "diagnosis", "critique"];
    for (let step of steps) {
      setActiveStep(step);
      await new Promise((r) => setTimeout(r, 1000));
    }

    try {
      const data = await analyzePatient(formData);
      setResult(data);
      saveToHistory(formData, data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setActiveStep(null);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">⚕️</span>
            <div>
              <h1>Clinical Decision Support</h1>
              <p>Multi-Agent AI System</p>
            </div>
          </div>
          <div className="badges">
            <span className="badge">LangGraph</span>
            <span className="badge">LangChain</span>
            <span className="badge">RAG</span>
            <span className="badge">FastAPI</span>
          </div>
        </div>
      </header>

      <main className="main">
        <PipelineTracker activeStep={activeStep} done={!!result} />
        <PatientForm onSubmit={handleSubmit} loading={loading} />
        {error && <div className="error-box">⚠️ {error}</div>}
        {result && <DiagnosisReport data={result} />}
        {history.length > 0 && (
          <CaseHistory
            history={history}
            onLoad={loadCase}
            onClear={clearHistory}
          />
        )}
      </main>

      <footer className="footer">
        Built with LangChain · LangGraph · FastAPI · React · FAISS · Groq
      </footer>
    </div>
  );
}