#!/usr/bin/env python3
import subprocess
import os
import json
import logging
from typing import List, Dict, Any

# Configure logging for structured output inside the sandbox
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

SCAN_DIR = os.getenv("SCAN_DIR", "/workspace")
REPORT_PATH = os.getenv("SCAN_REPORT", "/tmp/security_scan_report.json")

class ScannerOrchestrator:
    """Orchestrates security scanning tools for code-interpreter sandboxes."""

    def __init__(self, target_dir: str):
        self.target_dir = target_dir
        self.results = {
            "target": target_dir,
            "scans": {}
        }

    def run_command(self, cmd: List[str], tool_name: str) -> Dict[str, Any]:
        """Runs a scanning command and returns its exit code and summary."""
        logging.info(f"Running {tool_name} scan on {self.target_dir}...")
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False  # Tools might return non-zero for found issues
            )
            return {
                "exit_code": process.returncode,
                "stdout": process.stdout[:1000] if process.stdout else "",
                "stderr": process.stderr[:1000] if process.stderr else "",
                "status": "COMPLETED" if process.returncode == 0 else "ISSUES_FOUND"
            }
        except FileNotFoundError:
            logging.warning(f"{tool_name} not found on the PATH.")
            return {"status": "NOT_FOUND"}
        except Exception as e:
            logging.error(f"Error running {tool_name}: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def scan_semgrep(self):
        """Runs Semgrep static analysis."""
        # Try global bin path first
        cmd = ["/usr/local/bin/semgrep", "scan", "--config=auto", "--quiet", "--error", self.target_dir]
        res = self.run_command(cmd, "Semgrep")
        if res["status"] == "NOT_FOUND":
            cmd[0] = "semgrep"
            res = self.run_command(cmd, "Semgrep")
        self.results["scans"]["semgrep"] = res

    def scan_gitleaks(self):
        """Runs Gitleaks secret detection."""
        cmd = ["/usr/local/bin/gitleaks", "detect", "--source", self.target_dir, "--no-git", "--report-format", "json", "--no-banner"]
        res = self.run_command(cmd, "Gitleaks")
        if res["status"] == "NOT_FOUND":
            cmd[0] = "gitleaks"
            res = self.run_command(cmd, "Gitleaks")
        self.results["scans"]["gitleaks"] = res

    def scan_yamllint(self):
        """Runs YAMLlint for configuration files."""
        cmd = ["/usr/local/bin/yamllint", "-d", "{extends: relaxed, rules: {line-length: disable}}", self.target_dir]
        res = self.run_command(cmd, "YAMLlint")
        if res["status"] == "NOT_FOUND":
            cmd[0] = "yamllint"
            res = self.run_command(cmd, "YAMLlint")
        self.results["scans"]["yamllint"] = res

    def scan_bandit(self):
        """Runs Bandit for Python-specific security linting."""
        cmd = ["/usr/local/bin/bandit", "-r", self.target_dir, "-q"]
        res = self.run_command(cmd, "Bandit")
        if res["status"] == "NOT_FOUND":
            cmd[0] = "bandit"
            res = self.run_command(cmd, "Bandit")
        self.results["scans"]["bandit"] = res

    def scan_trivy(self):
        """Runs Trivy for filesystem vulnerabilities."""
        cmd = ["/usr/local/bin/trivy", "fs", "--scanners", "vuln,secret,config", "--quiet", self.target_dir]
        res = self.run_command(cmd, "Trivy")
        if res["status"] == "NOT_FOUND":
            cmd[0] = "trivy"
            res = self.run_command(cmd, "Trivy")
        self.results["scans"]["trivy"] = res

    def run_all(self):
        """Executes all registered scanners."""
        self.scan_semgrep()
        self.scan_gitleaks()
        self.scan_yamllint()
        self.scan_bandit()
        self.scan_trivy()
        self.save_results()

    def save_results(self):
        """Saves scan results to a JSON file and logs the final outcome."""
        with open(REPORT_PATH, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logging.info("=============================================")
        logging.info("  Security scanning cycle complete.")
        logging.info(f"  Report saved to: {REPORT_PATH}")
        logging.info("=============================================")

if __name__ == "__main__":
    orchestrator = ScannerOrchestrator(SCAN_DIR)
    orchestrator.run_all()
