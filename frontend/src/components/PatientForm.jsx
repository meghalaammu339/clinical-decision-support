import { useState } from "react";
import "./PatientForm.css";
import VoiceInput from "./Voiceinput";

const SAMPLE = {
  symptoms: "Chest pain radiating to left arm, sweating, shortness of breath",
  age: "58",
  gender: "Male",
  medical_history: "Hypertension, Type 2 Diabetes",
  current_medications: "Metformin 500mg, Amlodipine 5mg",
  duration: "2 hours",
};

export default function PatientForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    symptoms: "",
    age: "",
    gender: "Male",
    medical_history: "",
    current_medications: "",
    duration: "",
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ ...form, age: parseInt(form.age) });
  };

  const loadSample = () => setForm(SAMPLE);
  
  const handleVoice = (text) => {
  setForm({ ...form, symptoms: form.symptoms + " " + text });
};
  return (
    <div className="form-card">
      <div className="form-header">
        <h2>Patient Case Input</h2>
        <button type="button" className="btn-sample" onClick={loadSample}>
          Load Sample Case
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-group full">
  <div className="label-row">
    <label>Symptoms *</label>
    <VoiceInput onTranscript={handleVoice} />
  </div>
  <textarea
    name="symptoms"
    value={form.symptoms}
    onChange={handleChange}
    placeholder="Describe presenting symptoms in detail..."
    rows={3}
    required
  />
</div>

          <div className="form-group">
            <label>Age *</label>
            <input
              type="number"
              name="age"
              value={form.age}
              onChange={handleChange}
              placeholder="e.g. 45"
              min="0"
              max="120"
              required
            />
          </div>

          <div className="form-group">
            <label>Gender *</label>
            <select name="gender" value={form.gender} onChange={handleChange}>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div className="form-group">
            <label>Duration *</label>
            <input
              type="text"
              name="duration"
              value={form.duration}
              onChange={handleChange}
              placeholder="e.g. 2 hours, 3 days"
              required
            />
          </div>

          <div className="form-group">
            <label>Medical History</label>
            <input
              type="text"
              name="medical_history"
              value={form.medical_history}
              onChange={handleChange}
              placeholder="e.g. Hypertension, Diabetes"
            />
          </div>

          <div className="form-group full">
            <label>Current Medications</label>
            <input
              type="text"
              name="current_medications"
              value={form.current_medications}
              onChange={handleChange}
              placeholder="e.g. Metformin 500mg, Aspirin 75mg"
            />
          </div>
        </div>

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? (
            <span className="loading-text">
              <span className="spinner" />
              Running AI Agents...
            </span>
          ) : (
            "Run Clinical Analysis →"
          )}
        </button>
      </form>
    </div>
  );
}