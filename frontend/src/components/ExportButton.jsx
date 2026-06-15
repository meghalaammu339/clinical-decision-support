import jsPDF from "jspdf";
import "./ExportButton.css";

export default function ExportButton({ data }) {
  const handleExport = () => {
    const doc = new jsPDF();
    const report = data.final_report;
    const dx = data.differential_diagnosis?.differential_diagnosis || [];

    let y = 20;

    const addLine = (text, size = 12, bold = false) => {
      doc.setFontSize(size);
      doc.setFont("helvetica", bold ? "bold" : "normal");
      const lines = doc.splitTextToSize(String(text || ""), 170);
      doc.text(lines, 20, y);
      y += lines.length * (size * 0.5) + 4;
      if (y > 270) { doc.addPage(); y = 20; }
    };

    const addDivider = () => {
      doc.setDrawColor(100, 116, 139);
      doc.line(20, y, 190, y);
      y += 6;
    };

    // Header
    doc.setFillColor(30, 41, 59);
    doc.rect(0, 0, 210, 28, "F");
    doc.setTextColor(241, 245, 249);
    doc.setFontSize(15);
    doc.setFont("helvetica", "bold");
    doc.text("Clinical Decision Support Report", 20, 18);
    y = 38;
    doc.setTextColor(30, 41, 59);

    addLine(`Urgency: ${report?.urgency?.toUpperCase()}`, 13, true);
    addLine(`Primary Diagnosis: ${report?.primary_diagnosis}`, 13, true);
    if (data.confidence_score) {
      addLine(`AI Confidence Score: ${data.confidence_score}/100`, 12);
    }
    y += 4;
    addDivider();

    addLine("Clinical Summary", 13, true);
    addLine(report?.summary, 11);
    y += 4;
    addDivider();

    addLine("Differential Diagnoses", 13, true);
    dx.forEach((d) => {
      addLine(`#${d.rank} ${d.condition} — ${d.probability?.toUpperCase()} (${d.urgency})`, 11, true);
      addLine(`Supporting: ${d.supporting_evidence?.join(", ")}`, 10);
      addLine(`Tests: ${d.recommended_tests?.join(", ")}`, 10);
      y += 2;
    });
    addDivider();

    addLine("Recommended Investigations", 13, true);
    addLine(report?.recommended_tests?.join(", "), 11);
    y += 4;

    addLine("Immediate Actions", 13, true);
    report?.immediate_actions?.forEach((a, i) => addLine(`${i + 1}. ${a}`, 11));
    y += 4;

    if (report?.specialist_referral) {
      addLine("Specialist Referral", 13, true);
      addLine(report.specialist_referral, 11);
      y += 4;
    }

    if (report?.follow_up) {
      addLine("Follow Up", 13, true);
      addLine(report.follow_up, 11);
      y += 4;
    }

    addDivider();
    doc.setTextColor(100, 116, 139);
    addLine(report?.disclaimer, 9);
    doc.setFontSize(9);
    doc.text(`Generated: ${new Date().toLocaleString()}`, 20, 285);

    doc.save(`clinical_report_${Date.now()}.pdf`);
  };

  return (
    <button className="btn-export" onClick={handleExport}>
      📄 Export PDF
    </button>
  );
}