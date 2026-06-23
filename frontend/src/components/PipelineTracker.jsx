import "./PipelineTracker.css";

const NODE_LABELS = {
  input_guardrail: { label: "Input Guardrail", desc: "Validating input safety" },
  supervisor: { label: "Supervisor", desc: "Routing to next agent" },
  risk_agent: { label: "Risk Agent", desc: "Calculating patient risk" },
  intake_agent: { label: "Intake Agent", desc: "Structuring patient data" },
  research_agent: { label: "Research Agent", desc: "Searching evidence" },
  call_tools: { label: "Tool Call", desc: "Querying FAISS / PubMed" },
  extract_evidence: { label: "Extract Evidence", desc: "Processing results" },
  diagnosis_agent: { label: "Diagnosis Agent", desc: "Generating differentials" },
  critique_agent: { label: "Critique Agent", desc: "Validating diagnosis" },
  human_review: { label: "Human Review", desc: "Awaiting doctor approval" },
  output_guardrail: { label: "Output Guardrail", desc: "Safety check on report" },
};

const DISPLAY_NODES = [
  "input_guardrail",
  "risk_agent",
  "intake_agent",
  "research_agent",
  "diagnosis_agent",
  "critique_agent",
  "human_review",
  "output_guardrail",
];

export default function PipelineTracker({ activeNode, streamData, done }) {
  return (
    <div className="pipeline">
      {DISPLAY_NODES.map((key, i) => {
        const meta = NODE_LABELS[key];
        const isActive = activeNode === key;
        const isDone =
          done ||
          (activeNode && DISPLAY_NODES.indexOf(activeNode) > i);

        const liveDesc = (() => {
          if (isActive) return meta.desc;
          if (!isDone) return meta.desc;
          if (key === "risk_agent" && streamData?.risk_assessment)
            return `Score: ${streamData.risk_assessment.risk_score}`;
          if (key === "intake_agent" && streamData?.chief_complaint)
            return streamData.chief_complaint;
          if (key === "research_agent" && streamData?.evidence_count != null)
            return `${streamData.evidence_count} docs retrieved`;
          if (key === "diagnosis_agent" && streamData?.primary_diagnosis)
            return streamData.primary_diagnosis;
          if (key === "critique_agent" && streamData?.confidence_score != null)
            return `Confidence: ${streamData.confidence_score}%`;
          return meta.desc;
        })();

        return (
          <div key={key} className="pipeline-item">
            <div className={`pipeline-node ${isActive ? "active" : ""} ${isDone ? "done" : ""}`}>
              {isDone ? "✓" : i + 1}
            </div>
            <div className="pipeline-label">
              <p className="step-name">{meta.label}</p>
              <p className="step-desc">{liveDesc}</p>
            </div>
            {i < DISPLAY_NODES.length - 1 && (
              <div className={`pipeline-arrow ${isDone ? "arrow-done" : ""}`}>→</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
