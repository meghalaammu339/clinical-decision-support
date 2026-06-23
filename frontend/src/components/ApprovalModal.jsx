import { useState } from "react";
import "./ApprovalModal.css";

export default function ApprovalModal({ diagnosis, onDecide }) {
  const [notes, setNotes] = useState("");

  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <span className="modal-icon">🚨</span>
          <div>
            <h2>Emergent Case — Doctor Review Required</h2>
            <p>This case has been flagged as EMERGENT. Human approval is required before the report is finalized.</p>
          </div>
        </div>

        {diagnosis && (
          <div className="modal-diagnosis">
            <span>Suspected diagnosis:</span>
            <strong>{diagnosis}</strong>
          </div>
        )}

        <div className="modal-notes">
          <label>Doctor notes (optional)</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add any clinical notes, corrections, or observations..."
            rows={3}
          />
        </div>

        <div className="modal-actions">
          <button className="btn-reject" onClick={() => onDecide(false, notes)}>
            ✗ Reject &amp; Terminate
          </button>
          <button className="btn-approve" onClick={() => onDecide(true, notes)}>
            ✓ Approve &amp; Finalize Report
          </button>
        </div>
      </div>
    </div>
  );
}
