# Advanced FinOps Platform

AWS cost optimization and FinOps automation: resource discovery, cost analysis, ML right-sizing, anomaly detection, budget management, and safe execution with approval workflows.

**Development:** Use the **WSL terminal** with a **virtual environment (venv)**. All commands below assume you are in the project root inside WSL with venv activated.

## Structure

- **`main.py`** – Entry point and orchestration (run with `python main.py --help`)
- **`config.yaml`** – Platform configuration (AWS, services, optimization, logging)
- **`operational_dashboard.py`** – Monitoring and health dashboard
- **`aws/`** – AWS clients and service scanners (EC2, RDS, Lambda, S3, EBS, ELB, CloudWatch, billing, pricing, budgets)
- **`core/`** – Cost optimizer, pricing intelligence, ML right-sizing, anomaly detector, budget manager, execution engine, approval workflow, reporting, cost allocation
- **`utils/`** – Config, AWS config, HTTP client, monitoring, error recovery, safety controls, scheduler, workflow state
- **`tests/`** – Unit and integration tests (run: `pytest tests/` from project root)
- **`docs/`** – Implementation and task documentation

## Quick start (WSL / Linux)

From the project root in your WSL terminal:

```bash
# Create and activate virtual environment (do once)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py --optimize --approve-low   # Full run: discover, analyze, execute low-risk optimizations
python main.py --scan-only                # Discovery only (no changes)
python main.py --dry-run                  # Safe mode: no changes (for testing)
```

**Each new terminal:** activate the venv before running the app or tests:

```bash
cd /path/to/advanced-finops-bot
source .venv/bin/activate
```

## Real-time / continuous data

To keep data fresh (repeated discovery and analysis from AWS), use **continuous monitoring**. The app will re-run the full workflow on an interval so you get up-to-date costs and recommendations.

```bash
# Run every 60 minutes (default)
python main.py --continuous

# Run more frequently, e.g. every 15 minutes
python main.py --continuous --interval 15
```

This re-scans AWS, re-analyzes costs, and re-runs optimization logic on each cycle. Press **Ctrl+C** to stop.

To use a fixed schedule (daily optimization, weekly reports) instead, enable the options in `config.yaml` under `scheduling` and run:

```bash
python main.py --schedule
```

## Configuration

Use `config.yaml` in the project root or pass `--config path/to/config.yaml`. See `config.yaml` for AWS regions, service thresholds, optimization and safety settings.

## Tests

With venv activated, from the project root:

```bash
pytest tests/ -v
```

Run a single test file:

```bash
python tests/test_config_simple.py
```

Some tests require AWS credentials or mocks; see `tests/` for details.
