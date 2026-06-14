import "./PipelineTracker.css";

const STEPS = [
  { key: "intake", label: "Intake Agent", desc: "Structuring patient data" },
  { key: "rag", label: "RAG Agent", desc: "Retrieving evidence" },
  { key: "diagnosis", label: "Diagnosis Agent", desc: "Generating differentials" },
  { key: "critique", label: "Critique Agent", desc: "Validating diagnosis" },
];

export default function PipelineTracker({ activeStep, done }) {
  return (
    <div className="pipeline">
      {STEPS.map((step, i) => {
        const isActive = activeStep === step.key;
        const isDone = done || (
          activeStep &&
          STEPS.findIndex(s => s.key === activeStep) > i
        );

        return (
          <div key={step.key} className="pipeline-item">
            <div className={`pipeline-node ${isActive ? "active" : ""} ${isDone ? "done" : ""}`}>
              {isDone ? "✓" : i + 1}
            </div>
            <div className="pipeline-label">
              <p className="step-name">{step.label}</p>
              <p className="step-desc">{step.desc}</p>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`pipeline-arrow ${isDone ? "arrow-done" : ""}`}>→</div>
            )}
          </div>
        );
      })}
    </div>
  );
}