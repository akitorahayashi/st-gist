## CLAUDE.md Self-Modification Obligation

**Important**: This document governs the behavior of the claudecode agent itself. When changes are made to the codebase (adding dependencies, changing file structure, updating coding standards, etc.), claudecode is obligated to update this `CLAUDE.md` as part of the transaction to maintain consistency between the documentation and the implementation.

## Module Roles and Responsibilities

This `src/` directory contains the entire source code for the Streamlit web application. Its responsibility is to provide the application's user interface, business logic, and communication with external services. The architecture is designed to be modular and maintain a clear separation of concerns.

-   **`main.py`**: The application entry point. It handles session initialization and routes between the URL input page and the chat/query page.
-   **`components/`**: Manages all User Interface (UI) elements. Code here is responsible for rendering the Streamlit frontend and handling user interactions.
-   **`services/`**: Contains the core business logic. These modules are responsible for tasks like scraping, summarization, and conversation management.
-   **`clients/`**: Handles all communication with external APIs, specifically the Ollama API.
-   **`protocols/`**: Defines abstract interfaces (`Protocol` classes) for services and clients to ensure a consistent API and facilitate dependency injection and testing.

## Technology Stack and Environment

-   **Core Framework**: All UI must be built using the `streamlit` library.
-   **HTTP Communication**: Use `httpx` for all asynchronous HTTP requests to external APIs within the `clients` directory.
-   **HTML Parsing**: Use `BeautifulSoup4` for parsing and extracting text from HTML content within the `ScrapingService`.
-   **Configuration**: All configuration values (e.g., API endpoints, model names) must be read from environment variables. Never hardcode them. The `.env` file at the repository root is the source for these variables during local development.

## Architectural Principles and File Structure

Maintain a strict separation of concerns between UI, business logic, and external communication.

-   **Separation of Concerns**:
    -   **`components/`**: Contains only UI-related code. This layer is responsible for rendering widgets and handling the application's state via `st.session_state`. It orchestrates calls to the services.
    -   **`services/`**: Contains pure business logic. Services should be as framework-agnostic as possible. They are orchestrated by the UI components and may use clients to interact with external systems.
    -   **`clients/`**: Solely responsible for the details of communicating with external APIs (HTTP requests, error handling, payload formatting).
-   **Dependency Injection and Protocols**:
    -   For every service or client, create a corresponding interface in the `protocols/` directory.
    -   When a module depends on another component (e.g., a service depending on a client), it must depend on the `Protocol`, not the concrete implementation. This allows for interchangeable implementations, such as swapping a real client for a mock client.
-   **State Management**: The application's state must be managed exclusively through `st.session_state`. Avoid global variables. Services can be designed to read from or write to the session state, especially `ConversationService`, which is tightly coupled with the interactive chat loop.
-   **Error Handling**: Services must raise specific exceptions (e.g., `ValueError`, `SummarizationServiceError`) upon failure. The UI layer in `components/` is responsible for catching these exceptions and displaying user-friendly error messages via `st.error`.

## Coding Standards and Style Guide

-   **Formatting and Linting**: All code must conform to the Black and Ruff configurations defined in the root `pyproject.toml`. Run `make format` before committing.
-   **Logging**: Use the standard `logging` library to log errors and important information, especially within clients and services.
-   **Type Hinting**: All function signatures and variable declarations must include type hints.

## Testing Strategy and Procedures

-   All code added to the `src/` directory must be accompanied by corresponding tests located in the `tests/` directory.
-   The structure of the tests must mirror the `src/` directory structure.
-   For detailed testing guidelines, refer to the rules defined in `@tests/CLAUDE.md`.

## CI Process

-   All code in this directory is subject to the CI checks defined in the root of the repository. Refer to the root `CLAUDE.md` for details on the CI pipeline.

## Does Not Do

-   Services and clients must not contain any Streamlit UI code (e.g., `st.write`, `st.button`). All UI rendering is the exclusive responsibility of the `components/` modules. The one exception is `ConversationService`, which uses `st.rerun` and `st.session_state` to manage the interactive chat lifecycle.
-   Do not place business logic directly inside `components/` files. This logic must be encapsulated within a service in the `services/` directory and called from the component.
-   Do not hardcode configuration values. All configurable parameters must be loaded from environment variables.