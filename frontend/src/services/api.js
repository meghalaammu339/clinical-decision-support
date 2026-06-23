const API_BASE = "http://localhost:8000";

export const analyzePatient = async (patientData) => {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patientData),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Analysis failed");
  }
  return response.json();
};

export const analyzePatientStream = (patientData, callbacks) => {
  // callbacks = { onNode, onDone, onError, onAwaitingApproval, onThreadId }
  fetch(`${API_BASE}/analyze/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patientData),
  }).then(async (response) => {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      const lines = text.split("\n").filter((l) => l.startsWith("data: "));

      for (const line of lines) {
        try {
          const event = JSON.parse(line.replace("data: ", ""));
          if (event.type === "thread_id") {
            callbacks.onThreadId?.(event.thread_id);
          } else if (event.type === "node_complete") {
            callbacks.onNode?.(event);
          } else if (event.type === "final") {
            callbacks.onFinal?.(event.data);
          } else if (event.type === "awaiting_approval") {
            callbacks.onAwaitingApproval?.(event);
          } else if (event.type === "done") {
            callbacks.onDone?.();
          } else if (event.type === "error") {
            callbacks.onError?.(event.message);
          }
        } catch (_) {}
      }
    }
  }).catch(callbacks.onError);
};

export const approveCase = async (threadId, approved, doctorNotes = null) => {
  const response = await fetch(`${API_BASE}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id: threadId, approved, doctor_notes: doctorNotes }),
  });
  if (!response.ok) throw new Error("Approval failed");
  return response.json();
};
