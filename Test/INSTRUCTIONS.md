# Concurrency & Load Testing Instructions

This directory contains the tools necessary to verify that the CodeInspector API can handle production-level traffic bursts without crashing or hanging.

## 1. Prerequisites
Ensure you have the `requests` library installed on your machine:
```bash
pip install requests
```

---

## 2. Running the Load Test
The script simulates **50 concurrent users** hitting the API at the exact same time.

To run the test, navigate to this directory and execute:
```bash
python3 load_test_sim.py
```

### What to Look For:
- **API Response Time**: You should see an average response time of **less than 1000ms (1 second)**. 
- **Success Count**: The report should show `50/50` successes.
- **Non-Blocking Behavior**: The script will finish in just a few seconds. If it were still synchronous, it would take several minutes.

---

## 3. Verifying Results in Kubernetes
Once the script finishes, the API has accepted the work, but Kubernetes is still processing it in the background. Use these commands to monitor the progress:

### A. Monitor Pod Lifecycle
```bash
kubectl get pods -n opensandbox-system -w
```
You will see pods transition from `Pending` ➔ `ContainerCreating` ➔ `Running` ➔ `Completed`.

### B. Count Sandbox Resources
Verify that exactly 50 resources were created:
```bash
kubectl get batchsandbox -n opensandbox-system --no-headers | wc -l
```

### C. Check Security Reports
If you have access to the `/data` volume on the server, you can verify that the reports were generated:
```bash
ls /data/*/results/security_scan_report.json
```

---

## 4. Troubleshooting
- **401/403 Error**: Ensure the `OPEN-SANDBOX-API-KEY` in `load_test_sim.py` matches your server configuration.
- **Connection Refused**: Ensure the API Gateway is running on `localhost:8000`. If it's on a different port, update the `API_URL` in the script.
