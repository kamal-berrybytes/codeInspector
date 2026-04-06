# CodeInspector API - Modular Architecture Description

This document provides a detailed overview of the modularized FastAPI architecture used in the CodeInspector API. The system is designed to be a transparent gateway and management layer for the internal OpenSandbox service.

## Architecture Overview

The API is split into four primary modules to ensure a clean separation of concerns:

-   **`models.py`**: Data Transfer Objects (DTOs) and validation schemas.
-   **`config.py`**: Environment-based configuration and security headers.
-   **`backends.py`**: Logic for interacting with the execution clusters.
-   **`codeinspectior_api.py`**: The application entry point and routing layer.

---

## Component Details

### 1. `models.py`
This module defines the "language" used by the API. It uses **Pydantic** to enforce strict data validation for all incoming and outgoing requests.
-   **Execution Models**: `RunRequest` and `RunResponse` handle the core code execution requests.
-   **Sandbox Lifecycle**: `CreateSandboxRequest` and `SandboxResponse` define the requirements for provisioning new isolated environments.
-   **Enums**: `Language` restricts execution to specific supported runtimes (Python, JavaScript, Bash).

### 2. `config.py`
This module handles all external dependencies and environment-specific settings.
-   **Base URL**: `opensandbox_base_url()` dynamically resolves the upstream service address (usually a Kubernetes ClusterIP service).
-   **Headers**: `opensandbox_headers()` centralizes the management of the `OPEN-SANDBOX-API-KEY`, ensuring that every request to the backend is authenticated correctly.

### 3. `backends.py`
This module implements the **Strategy Pattern**.
-   **`SandboxBackend` (Abstract)**: An interface that defines what any execution backend *must* do (run code, create sandboxes, check health).
-   **`GenericHTTPBackend` (Concrete)**: The actual implementation that communicates with the OpenSandbox server via HTTP. It handles:
    -   Network timeouts.
    -   Error wrapping.
    -   Response parsing and mapping.

### 4. `codeinspectior_api.py`
This is the "brain" of the application. It initializes the FastAPI app and sets up the routes.
-   **App State**: Initializes the global `state.backend` based on configuration.
-   **Native Routes**: Provides high-level, typed endpoints like `/v1/sandboxes`.
-   **Transparent Proxy**: Contains the `_do_proxy` helper which forwards any request under `/backend/opensandbox/*` directly to the backend while injecting authentication and stripping unnecessary headers.
-   **Dynamic Documentation**: Bridges the gap between the local API and the remote service by fetching and patching the backend's `openapi.json` on the fly.

---

## Request Lifecycle (Example: Sandbox Creation)

1.  **Incoming Request**: A client sends a POST request to `/v1/sandboxes` with a JSON payload.
2.  **Validation**: FastAPI uses the `CreateSandboxRequest` model from `models.py` to validate the image spec and resource limits.
3.  **Backend Dispatch**: The route calls `state.backend.create_sandbox(req)`.
4.  **HTTP Transmission**: The `GenericHTTPBackend` (in `backends.py`) fetches the API key from `config.py`, wraps the request, and sends it to the internal OpenSandbox service.
5.  **Response Handling**: The response from the backend is parsed into a `SandboxResponse` and returned to the client.

## Benefits of this Modularization

-   **Readability**: Each file is focused on one task (Modeling, Config, Logic, or Routing).
-   **Maintainability**: You can change how backends work in `backends.py` without touching the route definitions in `codeinspectior_api.py`.
-   **Extensibility**: To add a new backend type (e.g., AWS Lambda or Docker), you simply create a new class in `backends.py` that inherits from `SandboxBackend`.
-   **DRY (Don't Repeat Yourself)**: Configuration and authentication logic are defined once in `config.py` and reused across both native routes and the proxy system.
