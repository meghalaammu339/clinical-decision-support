import { useState } from "react";
import "./PipelineTracker.css";

const NODES = [
  { key: "input_guardrail", label: "Input Guardrail" },
  { key: "risk_agent", label: "Risk Agent" },
  { key: "intake_agent", label: "Intake Agent" },
  { key: "research_agent", label: "Research Agent" },
  { key: "diagnosis_agent", label: "Diagnosis Agent" },
  { key: "critique_agent", label: "Critique Agent" },
  { key: "human_review", label: "Human Review" },
  { key: "output_guardrail", label: "Output Guardrail" },
];

export default function PipelineTracker({ activeNode, streamData, done }) {
  const [tooltip, setTooltip] = useState(null);

  return (
    <div className="pipeline">
      {NODES.map((node, i) => {
        const isActive = activeNode === node.key;
        const isDone = done || (activeNode && NODES.findIndex(n => n.key === activeNode) > i);

        const liveDesc = (() => {
          if (node.key === "risk_agent" && streamData?.risk_assessment)
            return `Score: ${streamData.risk_assessment.risk_score}`;
          if (node.key === "diagnosis_agent" && streamData?.primary_diagnosis)
            return streamData.primary_diagnosis;
          if (node.key === "critique_agent" && streamData?.confidence_score != null)
            return `Confidence: ${streamData.confidence_score}%`;
          return null;
        })();

        return (
          <div key={node.key} className="pipeline-item">
            <div className="pipeline-step">
              <div
                className={`pipeline-node ${isActive ? "active" : ""} ${isDone ? "done" : ""}`}
                onMouseEnter={() => setTooltip(i)}
                onMouseLeave={() => setTooltip(null)}
                onClick={() => setTooltip(tooltip === i ? null : i)}
              >
                {isDone ? "✓" : i + 1}
              </div>
              {tooltip === i && (
                <div className="pipeline-tooltip">
                  <strong>{node.label}</strong>
                  {liveDesc && <span>{liveDesc}</span>}
                </div>
              )}
            </div>
            {i < NODES.length - 1 && (
              <div className={`pipeline-arrow ${isDone ? "arrow-done" : ""}`}>→</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
