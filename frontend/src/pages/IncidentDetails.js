import React, { useState, useEffect } from "react";
import axios from "axios";
import { useParams } from "react-router-dom";

const IncidentDetail = () => {
  const { id } = useParams();
  const [incident, setIncident] = useState(null);
  const [analysis, setAnalysis] = useState("");
  const [timer, setTimer] = useState(null);

  useEffect(() => {
    fetchIncident();
  }, [id]);

  const fetchIncident = async () => {
    try {
      const response = await axios.get(
        `http://localhost:8000/incidents/api/incidents/${id}/`
      );
      setIncident(response.data);
      if (response.data.ticket && response.data.ticket.deadline_timestamp) {
        startTimer(response.data.ticket.deadline_timestamp);
      }
    } catch (error) {
      console.error("Error fetching incident:", error);
    }
  };

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
    return () => clearInterval(interval);
  };

  const handleAction = async (action) => {
    try {
      await axios.post(
        `http://localhost:8000/incidents/api/ticket/${incident.ticket.id}/${action}/`
      );
      fetchIncident();
    } catch (error) {
      console.error(`Error performing ${action}:`, error);
    }
  };

  const handleClassify = async (classification) => {
    try {
      await axios.post(
        `http://localhost:8000/incidents/api/ticket/${incident.ticket.id}/complete/`,
        {
          classification,
          notes: analysis,
        }
      );
      fetchIncident();
    } catch (error) {
      console.error("Error classifying incident:", error);
    }
  };

  if (!incident) return <div>Loading...</div>;

  return (
    <div className="incident-details">
      <h1>{incident.incident_type || `Incident ${incident.id}`}</h1>
      {incident.ticket && (
        <p>
          SLA Timer:{" "}
          {timer !== null
            ? `${Math.floor(timer / 3600)}h ${Math.floor(
                (timer % 3600) / 60
              )}m ${timer % 60}s`
            : "Calculating..."}
        </p>
      )}
      <p>Status: {incident.status}</p>
      <p>Severity: {incident.severity}</p>
      <div className="actions">
        {incident.ticket.status === "ASSIGNED" && (
          <button onClick={() => handleAction("start")}>Start</button>
        )}
        {incident.ticket.status === "IN_PROGRESS" && (
          <button onClick={() => handleAction("pause")}>Pause</button>
        )}
      </div>
      <textarea
        value={analysis}
        onChange={(e) => setAnalysis(e.target.value)}
        placeholder="Write your analysis here"
      />
      {incident.ticket.status === "IN_PROGRESS" && (
        <div className="classification">
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
      <div className="analyses">
        <h3>Analyses</h3>
        {incident.analyses.map((analysis) => (
          <div key={analysis.id}>
            <p>{analysis.notes}</p>
            <p>
              By: {analysis.analyst} at{" "}
              {new Date(analysis.timestamp).toLocaleString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default IncidentDetail;
