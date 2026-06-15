
import "./ConfidenceGauge.css";

export default function ConfidenceGauge({ score }) {
  if (!score) return null;

  const getColor = (score) => {
    if (score >= 80) return "#22c55e";
    if (score >= 60) return "#f97316";
    return "#ef4444";
  };

  const getLabel = (score) => {
    if (score >= 80) return "High Confidence";
    if (score >= 60) return "Moderate Confidence";
    return "Low Confidence";
  };

  // SVG arc math
  const radius = 60;
  const circumference = Math.PI * radius; // half circle
  const progress = (score / 100) * circumference;
  const color = getColor(score);

  return (
    <div className="gauge-wrapper">
      <h3>AI Confidence Score</h3>
      <div className="gauge-container">
        <svg width="160" height="90" viewBox="0 0 160 90">
          {/* Background arc */}
          <path
            d="M 10 80 A 70 70 0 0 1 150 80"
            fill="none"
            stroke="#334155"
            strokeWidth="12"
            strokeLinecap="round"
          />
          {/* Progress arc */}
          <path
            d="M 10 80 A 70 70 0 0 1 150 80"
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={`${(score / 100) * 220} 220`}
            style={{ transition: "stroke-dasharray 1s ease" }}
          />
          {/* Score text */}
          <text x="80" y="75" textAnchor="middle" fontSize="24" fontWeight="700" fill={color}>
            {score}
          </text>
        </svg>
        <p className="gauge-label" style={{ color }}>{getLabel(score)}</p>
      </div>
    </div>
  );
}

