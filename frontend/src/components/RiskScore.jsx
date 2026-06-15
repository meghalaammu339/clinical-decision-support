// Feature 4: Risk Score Display
// Add to DiagnosisReport.jsx after the header
// Data comes from risk_assessment field in API response

import "./RiskScore.css";

const RISK_COLORS = {
  low: "#22c55e",
  moderate: "#f97316",
  high: "#ef4444",
  critical: "#7c3aed",
};

export default function RiskScore({ riskData }) {
  if (!riskData) return null;

  const { risk_score, risk_level, risk_factors, protective_factors, risk_summary } = riskData;
  const color = RISK_COLORS[risk_level] || "#6b7280";

  return (
    <div className="risk-section">
      <h3>Patient Risk Assessment</h3>
      <div className="risk-content">

        {/* Score Circle */}
        <div className="risk-score-circle" style={{ borderColor: color }}>
          <span className="risk-number" style={{ color }}>{risk_score}</span>
          <span className="risk-label" style={{ color }}>{risk_level?.toUpperCase()}</span>
        </div>

        <div className="risk-details">
          <p className="risk-summary">{risk_summary}</p>

          {/* Progress Bar */}
          <div className="risk-bar-wrapper">
            <div className="risk-bar-track">
              <div
                className="risk-bar-fill"
                style={{
                  width: `${risk_score}%`,
                  background: color
                }}
              />
            </div>
            <div className="risk-bar-labels">
              <span>Low</span>
              <span>Moderate</span>
              <span>High</span>
              <span>Critical</span>
            </div>
          </div>

          {/* Factors */}
          <div className="risk-factors">
            <div>
              <p className="factor-label risk">⚠ Risk Factors</p>
              <ul>
                {risk_factors?.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
            <div>
              <p className="factor-label protective">✓ Protective Factors</p>
              <ul>
                {protective_factors?.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// HOW TO USE IN DiagnosisReport.jsx:
// 1. import RiskScore from "./RiskScore";
// 2. const riskData = data.risk_assessment;
// 3. Add after report header: <RiskScore riskData={riskData} />