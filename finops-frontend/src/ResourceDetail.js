import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

function ResourceDetail({ resource, onBack }) {
  const [instanceData, setInstanceData] = useState(null);
  const [resizeOptions, setResizeOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedResize, setSelectedResize] = useState(null);
  const [resizingInProgress, setResizingInProgress] = useState(false);

  useEffect(() => {
    const loadResourceData = async () => {
      if (!resource || !resource.id) {
        setLoading(false);
        return;
      }

      try {
        // Fetch instance details
        const instanceRes = await axios.get(
          `http://localhost:5000/api/instances/${resource.id}`
        );
        setInstanceData(instanceRes.data.data);

        // Fetch resize options
        const resizeRes = await axios.get(
          `http://localhost:5000/api/instances/${resource.id}/resize-options`
        );
        setResizeOptions(resizeRes.data.data.resize_options || []);
      } catch (error) {
        console.error("❌ Failed to load resource data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadResourceData();
  }, [resource]);

  const handleResize = async (targetType) => {
    if (!instanceData) return;

    setResizingInProgress(true);
    try {
      const response = await axios.post(
        `http://localhost:5000/api/instances/${instanceData.instance_id}/resize`,
        {
          new_instance_type: targetType,
        }
      );

      console.log("✅ Resize request submitted:", response.data);
      alert(
        `Resize request submitted: ${instanceData.instance_type} → ${targetType}`
      );
      setSelectedResize(null);
    } catch (error) {
      console.error("❌ Resize request failed:", error);
      alert("Failed to submit resize request. Please try again.");
    } finally {
      setResizingInProgress(false);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <button className="btn-back" onClick={onBack}>
          ← Back to Dashboard
        </button>
        <p>Loading resource details...</p>
      </div>
    );
  }

  if (!instanceData) {
    return (
      <div className="page">
        <button className="btn-back" onClick={onBack}>
          ← Back to Dashboard
        </button>
        <p>Resource not found.</p>
      </div>
    );
  }

  return (
    <div className="page">
      <button className="btn-back" onClick={onBack}>
        ← Back to Dashboard
      </button>

      <div className="detail-header">
        <h1>📊 Resource Details</h1>
        <p className="resource-id">{instanceData.instance_id}</p>
      </div>

      {/* INSTANCE INFORMATION */}
      <div className="detail-card">
        <h2>Instance Information</h2>
        <div className="detail-grid">
          <div className="detail-item">
            <span className="label">Instance ID</span>
            <span className="value">{instanceData.instance_id}</span>
          </div>
          <div className="detail-item">
            <span className="label">Instance Type</span>
            <span className="value">{instanceData.instance_type}</span>
          </div>
          <div className="detail-item">
            <span className="label">Region</span>
            <span className="value">{instanceData.region}</span>
          </div>
          <div className="detail-item">
            <span className="label">State</span>
            <span className="value status-badge">{instanceData.state}</span>
          </div>
          <div className="detail-item">
            <span className="label">CPU Utilization</span>
            <span className="value">{instanceData.cpu || "N/A"}%</span>
          </div>
          <div className="detail-item">
            <span className="label">Last Updated</span>
            <span className="value">
              {new Date(instanceData.timestamp).toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* COST INFORMATION */}
      <div className="detail-card">
        <h2>💰 Cost Information</h2>
        <div className="detail-grid">
          <div className="detail-item">
            <span className="label">Hourly Cost</span>
            <span className="value cost-highlight">
              ${instanceData.hourly_cost?.toFixed(4) || "0.00"}
            </span>
          </div>
          <div className="detail-item">
            <span className="label">Monthly Cost</span>
            <span className="value cost-highlight">
              ${instanceData.monthly_cost?.toFixed(2) || "0.00"}
            </span>
          </div>
          <div className="detail-item">
            <span className="label">Annual Cost</span>
            <span className="value cost-highlight">
              ${instanceData.annual_cost?.toFixed(2) || "0.00"}
            </span>
          </div>
        </div>
      </div>

      {/* RESIZE OPTIONS */}
      {resizeOptions.length > 0 && (
        <div className="detail-card">
          <h2>🔄 Resize Opportunities</h2>
          <p className="section-description">
            Based on current utilization, this instance can be resized to save
            costs.
          </p>

          <div className="resize-options-grid">
            {resizeOptions.map((option, idx) => (
              <div
                key={idx}
                className={`resize-option ${
                  selectedResize === option.target_instance_type
                    ? "selected"
                    : ""
                }`}
                onClick={() => setSelectedResize(option.target_instance_type)}
              >
                <div className="resize-header">
                  <h4>{option.target_instance_type}</h4>
                  <span className="savings-badge">
                    Save {option.savings_percentage}%
                  </span>
                </div>

                <div className="resize-details">
                  <div className="resize-row">
                    <span>Current Monthly:</span>
                    <span className="cost">
                      ${option.current_monthly_cost.toFixed(2)}
                    </span>
                  </div>
                  <div className="resize-row">
                    <span>Target Monthly:</span>
                    <span className="cost-new">
                      ${option.target_monthly_cost.toFixed(2)}
                    </span>
                  </div>
                  <div className="resize-row highlight">
                    <span>Monthly Savings:</span>
                    <span className="savings">
                      ${option.estimated_monthly_savings.toFixed(2)}
                    </span>
                  </div>
                  <div className="resize-row">
                    <span>Annual Savings:</span>
                    <span className="savings">
                      ${option.estimated_annual_savings.toFixed(2)}
                    </span>
                  </div>
                  <div className="resize-row">
                    <span>Downtime:</span>
                    <span>{option.downtime_estimate}</span>
                  </div>
                </div>

                {selectedResize === option.target_instance_type && (
                  <button
                    className="btn-resize"
                    onClick={() => handleResize(option.target_instance_type)}
                    disabled={resizingInProgress}
                  >
                    {resizingInProgress ? "Processing..." : "Confirm Resize"}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {resizeOptions.length === 0 && (
        <div className="detail-card">
          <p className="no-options">
            No resize opportunities available for this instance.
          </p>
        </div>
      )}

      {/* AWS CONSOLE LINK */}
      <div className="detail-card">
        <a
          href={`https://console.aws.amazon.com/ec2/v2/home?region=${instanceData.region}#InstanceDetails:instanceId=${instanceData.instance_id}`}
          target="_blank"
          rel="noreferrer"
          className="btn-aws-console"
        >
          Open in AWS Console →
        </a>
      </div>
    </div>
  );
}

export default ResourceDetail;
