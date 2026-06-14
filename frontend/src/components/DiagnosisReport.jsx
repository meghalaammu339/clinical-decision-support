import "./DiagnosisReport.css";

const URGENCY_COLOR = {
  emergent: "#ef4444",
  urgent: "#f97316",
  routine: "#22c55e",
};

const PROB_COLOR = {
  high: "#ef4444",
  medium: "#f97316",
  low: "#6b7280",
};

export default function DiagnosisReport({ data }) {
  const { structured_case, differential_diagnosis, final_report, critique } = data;
  const differentials = differential_diagnosis?.differential_diagnosis || [];
  const urgency = final_report?.urgency || "routine";

  return (
    <div className="report">

      {/* Header */}
      <div className="report-header">
        <div className="report-title">
          <span>🏥</span>
          <div>
            <h2>Clinical Decision Support Report</h2>
            <p>AI-Assisted Analysis — Not a substitute for clinical judgment</p>
          </div>
        </div>
        <div
          className="urgency-badge"
          style={{ background: URGENCY_COLOR[urgency] }}
        >
          {urgency.toUpperCase()}
        </div>
      </div>

      {/* Summary */}
      {final_report?.summary && (
        <div className="section">
          <h3>Clinical Summary</h3>
          <p className="summary-text">{final_report.summary}</p>
        </div>
      )}

      {/* Primary Diagnosis */}
      {final_report?.primary_diagnosis && (
        <div className="section">
          <h3>Primary Diagnosis</h3>
          <div className="primary-dx">
            <span>🎯</span>
            <span className="primary-dx-name">{final_report.primary_diagnosis}</span>
          </div>
        </div>
      )}

      {/* Differentials */}
      {differentials.length > 0 && (
        <div className="section">
          <h3>Differential Diagnoses</h3>
          <div className="diff-list">
            {differentials.map((dx, i) => (
              <div key={i} className="diff-card">
                <div className="diff-header">
                  <span className="diff-rank">#{dx.rank}</span>
                  <span className="diff-condition">{dx.condition}</span>
                  <span className="diff-prob" style={{ color: PROB_COLOR[dx.probability] }}>
                    {dx.probability?.toUpperCase()}
                  </span>
                  <span
                    className="diff-urgency"
                    style={{
                      borderColor: URGENCY_COLOR[dx.urgency],
                      color: URGENCY_COLOR[dx.urgency]
                    }}
                  >
                    {dx.urgency}
                  </span>
                </div>

                <div className="diff-evidence">
                  <div>
                    <p className="evidence-label for">✓ Supporting</p>
                    <ul>
                      {dx.supporting_evidence?.map((e, j) => <li key={j}>{e}</li>)}
                    </ul>
                  </div>
                  <div>
                    <p className="evidence-label against">✗ Against</p>
                    <ul>
                      {dx.against_evidence?.map((e, j) => <li key={j}>{e}</li>)}
                    </ul>
                  </div>
                </div>

                <div className="diff-footer">
                  <span>📚 {dx.cited_source}</span>
                  <span>🔬 {dx.recommended_tests?.join(", ")}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tests */}
      {final_report?.recommended_tests?.length > 0 && (
        <div className="section">
          <h3>Recommended Investigations</h3>
          <div className="tag-list">
            {final_report.recommended_tests.map((t, i) => (
              <span key={i} className="tag">{t}</span>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      {final_report?.immediate_actions?.length > 0 && (
        <div className="section">
          <h3>Immediate Actions</h3>
          <ol className="action-list">
            {final_report.immediate_actions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ol>
        </div>
      )}

      {/* Referral */}
      {final_report?.specialist_referral && (
        <div className="section">
          <h3>Specialist Referral</h3>
          <p className="referral">👨‍⚕️ {final_report.specialist_referral}</p>
        </div>
      )}

      {/* Critique */}
      {critique && (
        <div className="section critique">
          <h3>🤖 AI Critique Agent Assessment</h3>
          <p>{critique}</p>
        </div>
      )}

      {/* Disclaimer */}
      <div className="disclaimer">
        ⚠️ {final_report?.disclaimer}
      </div>
    </div>
  );
}