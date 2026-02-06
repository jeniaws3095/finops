from flask import Flask, jsonify
from datetime import datetime
from main import AdvancedFinOpsOrchestrator

app = Flask(__name__)

# Initialize orchestrator ONCE (important for performance)
orchestrator = AdvancedFinOpsOrchestrator(
    region="us-east-1",
    dry_run=True
)


@app.route("/health", methods=["GET"])
def health():
    return {
        "status": "ok",
        "service": "finops-bot",
        "time": datetime.utcnow().isoformat()
    }


@app.route("/dashboard", methods=["GET"])
def dashboard():
    """
    Fully bot-driven dashboard endpoint
    Backend -> Python bot -> AWS / ML / Analysis
    """

    print("🔥 DASHBOARD REQUEST RECEIVED BY PYTHON BOT")

    # ---------------------------
    # 1️⃣ Resource discovery
    # ---------------------------
    discovery = orchestrator.run_discovery()
    resource_count = discovery.get("resources_discovered", 0)

    # ---------------------------
    # 2️⃣ Optimization analysis
    # ---------------------------
    optimization = orchestrator.run_optimization_analysis()
    optimization_count = optimization.get("optimizations_found", 0)
    monthly_savings = optimization.get("potential_monthly_savings", 0.0)

    # ---------------------------
    # 3️⃣ Anomaly detection
    # ---------------------------
    anomaly_results = orchestrator.run_anomaly_detection()
    active_anomalies = anomaly_results.get("anomalies_detected", 0)
    anomaly_cost_impact = anomaly_results.get("total_cost_impact", 0.0)

    # ---------------------------
    # 4️⃣ Budget management
    # ---------------------------
    budget_results = orchestrator.run_budget_management()
    budget_summary = budget_results.get("budget_summary", {})

    budget_utilization = budget_summary.get(
        "average_utilization", 0.0
    )

    # ---------------------------
    # 5️⃣ Total cost (AWS Cost Explorer – placeholder hook)
    # ---------------------------
    # NOTE:
    # You already have AWSConfig wired.
    # This is the CORRECT place to plug Cost Explorer later.
    total_cost = anomaly_cost_impact + monthly_savings * 3  # temporary safe estimate

    # ---------------------------
    # Final dashboard payload
    # ---------------------------
    dashboard_data = {
        "totalCost": round(total_cost, 2),
        "monthlySavings": round(monthly_savings, 2),
        "optimizationOpportunities": optimization_count,
        "activeAnomalies": active_anomalies,
        "resourceCount": resource_count,
        "budgetUtilization": round(budget_utilization, 2),
        "lastUpdated": datetime.utcnow().isoformat()
    }

    return jsonify({
        "success": True,
        "source": "python-finops-bot",
        "data": dashboard_data
    })

@app.route("/metrics", methods=["GET"])
def metrics():
    """
    Backend → calls this
    Provides dashboard metrics KPIs
    Frontend expects:
      - costTrend
      - savingsRate
      - efficiencyScore
      - optimizationRate
      - anomalyDetectionRate
    """
    try:
        optimization = orchestrator.run_optimization_analysis()

        optimizations_found = optimization.get("optimizations_found", 0)
        potential_savings = optimization.get("potential_monthly_savings", 0)

        # Defensive calculations
        efficiency_score = min(
            100,
            round((potential_savings / 1000) * 10, 1)
        ) if potential_savings > 0 else 0

        metrics = {
            "costTrend": "+12.3%",  # replace later with real trend engine
            "savingsRate": f"+{round((potential_savings / 5000) * 100, 1)}%",
            "efficiencyScore": efficiency_score,
            "optimizationRate": min(100, optimizations_found * 5),
            "anomalyDetectionRate": 95.0
        }

        return jsonify({
            "source": "python-finops-bot",
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logging.exception("Metrics generation failed")
        return jsonify({
            "source": "python-finops-bot",
            "error": str(e),
            "data": {}
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000)
