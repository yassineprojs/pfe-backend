import React, { useState, useEffect } from "react";
import axios from "axios";
import { useParams } from "react-router-dom";

const IncidentDetail = () => {
  const { id } = useParams();
  const [incident, setIncident] = useState(null);
  const [analysis, setAnalysis] = useState("");
  const [timer, setTimer] = useState(null);
  const [playbooks, setPlaybooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Fetch incident data on mount and poll every 30 seconds for real-time updates
  useEffect(() => {
    fetchIncident();
    const pollInterval = setInterval(fetchIncident, 30000); // 30-second polling
    return () => clearInterval(pollInterval); // Cleanup on unmount
  }, [id]);

  // Fetch incident details
  const fetchIncident = async () => {
    try {
      const response = await axios.get(
        `http://localhost:8000/incidents/api/incidents/${id}/`,
        {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        }
      );
      setIncident(response.data);
      if (response.data.ticket && response.data.ticket.deadline_timestamp) {
        startTimer(response.data.ticket.deadline_timestamp);
      }
      fetchPlaybooks(response.data.incident_type); // Fetch related playbooks
      setLoading(false);
    } catch (err) {
      console.error("Error fetching incident:", err);
      setError("Failed to load incident details.");
      setLoading(false);
    }
  };

  // Fetch playbooks based on incident type
  const fetchPlaybooks = async (incidentType) => {
    try {
      const response = await axios.get(
        `http://localhost:8000/threat-intel/api/playbooks/?incident_type=${incidentType}`,
        {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        }
      );
      setPlaybooks(response.data);
    } catch (err) {
      console.error("Error fetching playbooks:", err);
      setPlaybooks([]);
    }
  };

  // Start SLA timer
  const startTimer = (deadline) => {
    const endTime = new Date(deadline).getTime();
    const interval = setInterval(() => {
      const now = new Date().getTime();
      const timeLeft = endTime - now;
      if (timeLeft <= 0) {
        clearInterval(interval);
        setTimer(0);
      } else {
        setTimer(Math.floor(timeLeft / 1000));
      }
    }, 1000);
    return () => clearInterval(interval); // Cleanup on unmount
  };

  // Format timer into a readable string
  const formatTime = (seconds) => {
    if (seconds <= 0) return "Overdue";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h}h ${m}m ${s}s`;
  };

  // Handle ticket actions (start, pause, complete)
  const handleAction = async (action) => {
    try {
      await axios.post(
        `http://localhost:8000/incidents/api/ticket/${incident.ticket.id}/${action}/`,
        {},
        {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        }
      );
      setError(""); // Clear any previous errors
      fetchIncident(); // Refresh data after action
    } catch (err) {
      console.error(`Error performing ${action}:`, err);
      setError(`Failed to ${action} the ticket.`);
    }
  };

  // Handle incident classification and analysis submission
  const handleClassify = async (classification) => {
    try {
      await axios.post(
        `http://localhost:8000/incidents/api/ticket/${incident.ticket.id}/complete/`,
        { classification, notes: analysis },
        {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        }
      );
      setAnalysis(""); // Clear analysis field
      setError("");
      fetchIncident();
    } catch (err) {
      console.error("Error classifying incident:", err);
      setError("Failed to classify the incident.");
    }
  };

  // Loading and error states
  if (loading) return <div>Loading incident details...</div>;
  if (error && !incident) return <div className="error">{error}</div>;
  if (!incident) return <div>Incident not found.</div>;

  return (
    <div className="incident-details">
      <h1>{incident.incident_type || `Incident ${incident.id}`}</h1>

      {/* Incident Information */}
      <div className="incident-info">
        <p>
          <strong>Status:</strong> {incident.status}
        </p>
        <p>
          <strong>Severity:</strong> {incident.severity}
        </p>
        <p>
          <strong>Assigned Analysts:</strong>{" "}
          {incident.ticket?.assigned_analysts?.join(", ") || "Unassigned"}
        </p>
        {incident.ticket && (
          <p
            className={`sla-timer ${
              timer <= 0 ? "overdue" : timer < 3600 ? "warning" : ""
            }`}
          >
            <strong>SLA Remaining:</strong> {formatTime(timer)}
          </p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="actions">
        {incident.ticket.status === "ASSIGNED" && (
          <button onClick={() => handleAction("start")}>Start Work</button>
        )}
        {incident.ticket.status === "IN_PROGRESS" && (
          <>
            <button onClick={() => handleAction("pause")}>Pause Work</button>
            {/* "Complete" is handled via classification below */}
          </>
        )}
      </div>

      {/* Analysis Section */}
      <div className="analysis-section">
        <h3>Write Analysis</h3>
        <textarea
          value={analysis}
          onChange={(e) => setAnalysis(e.target.value)}
          placeholder="Enter your analysis here..."
          rows="5"
        />
        {incident.ticket.status === "IN_PROGRESS" && (
          <div className="classification-buttons">
            <button onClick={() => handleClassify("False Positive")}>
              False Positive
            </button>
            <button onClick={() => handleClassify("true_positive_legitimate")}>
              True Positive Legitimate
            </button>
            <button onClick={() => handleClassify("true_positive_phishing")}>
              True Positive Phishing
            </button>
          </div>
        )}
      </div>

      {/* Playbooks Section */}
      <div className="playbooks-section">
        <h3>Related Playbooks</h3>
        {playbooks.length > 0 ? (
          <ul>
            {playbooks.map((playbook) => (
              <li key={playbook.id}>
                <a
                  href={`/playbooks/${playbook.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {playbook.name}
                </a>
                {/* Add a "Start Playbook" button if your backend supports it */}
              </li>
            ))}
          </ul>
        ) : (
          <p>No playbooks available for this incident type.</p>
        )}
      </div>

      {/* Analyses History */}
      <div className="analyses-history">
        <h3>Analyses History</h3>
        {incident.analyses.length > 0 ? (
          incident.analyses.map((analysis) => (
            <div key={analysis.id} className="analysis-item">
              <p>{analysis.notes}</p>
              <p>
                <em>
                  By {analysis.analyst} on{" "}
                  {new Date(analysis.timestamp).toLocaleString()}
                </em>
              </p>
            </div>
          ))
        ) : (
          <p>No analyses submitted yet.</p>
        )}
      </div>

      {/* Error Feedback */}
      {error && <div className="error">{error}</div>}
    </div>
  );
};

export default IncidentDetail;
