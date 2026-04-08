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
SCAN_TOOLS_ENV = os.getenv("SCAN_TOOLS", "") # Comma-separated list of tools to run

class ScannerOrchestrator:
    """Orchestrates security scanning tools for code-interpreter sandboxes."""

    def __init__(self, target_dir: str):
        self.target_dir = target_dir
        self.results = {
            "target": target_dir,
            "files_scanned": [],
            "scans": {}
        }
        self.enabled_tools = self._get_enabled_tools()

    def _get_enabled_tools(self) -> List[str]:
        """Determines which tools should be run based on env vars and file types."""
        all_files = []
        for root, _, files in os.walk(self.target_dir):
            for file in files:
                all_files.append(os.path.join(root, file))
        
        self.results["files_scanned"] = [os.path.relpath(f, self.target_dir) for f in all_files]
        
        logging.info("=============================================")
        logging.info(f" Discovering files in {self.target_dir}:")
        for f in self.results["files_scanned"]:
            logging.info(f"  - {f}")
        logging.info("=============================================")

        if SCAN_TOOLS_ENV:
            requested = [t.strip().lower() for t in SCAN_TOOLS_ENV.split(",") if t.strip()]
            logging.info(f" User specified tools: {requested}")
            return requested

        # Auto-detection logic
        enabled = ["semgrep", "gitleaks", "trivy"] # Core tools enabled by default
        
        has_python = any(f.endswith(".py") for f in self.results["files_scanned"])
        has_yaml = any(f.endswith((".yaml", ".yml")) for f in self.results["files_scanned"])
        
        if has_python:
            logging.info("  [Auto-Detect] Python files found. Enabling Bandit.")
            enabled.append("bandit")
        if has_yaml:
            logging.info("  [Auto-Detect] YAML files found. Enabling YAMLlint.")
            enabled.append("yamllint")
            
        return enabled

    def run_command(self, cmd: List[str], tool_name: str) -> Dict[str, Any]:
        """Runs a scanning command and returns its exit code and summary."""
        logging.info(f" Running {tool_name} scan...")
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
            logging.warning(f" {tool_name} not found on the PATH.")
            return {"status": "NOT_FOUND"}
        except Exception as e:
            logging.error(f" Error running {tool_name}: {str(e)}")
            return {"status": "ERROR", "error": str(e)}

    def scan_semgrep(self):
        """Runs Semgrep static analysis."""
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
        """Executes enabled scanners."""
        if "semgrep" in self.enabled_tools: self.scan_semgrep()
        if "gitleaks" in self.enabled_tools: self.scan_gitleaks()
        if "yamllint" in self.enabled_tools: self.scan_yamllint()
        if "bandit" in self.enabled_tools: self.scan_bandit()
        if "trivy" in self.enabled_tools: self.scan_trivy()
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

if __name__ == "__main__":
    orchestrator = ScannerOrchestrator(SCAN_DIR)
    orchestrator.run_all()
