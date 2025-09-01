## CLAUDE.md Self-Modification Obligation

**Important**: This document governs the behavior of the claudecode agent itself. When changes are made to the codebase (adding dependencies, changing file structure, updating coding standards, etc.), claudecode is obligated to update this `CLAUDE.md` as part of the transaction to maintain consistency between the documentation and the implementation.

## Project Overview and Mission

This project is a web page summarization tool built with Streamlit. Its mission is to accept a public URL from a user, scrape and summarize the content of the web page using an AI model via Ollama, and then provide an interactive chat interface where the user can ask questions about the summarized content.

## Technology Stack and Environment

-   **Language**: Python 3.12.11.
-   **Dependency Management**: Use uv for managing dependencies. All dependencies are defined in `pyproject.toml` and locked in `uv.lock`.
-   **Primary Framework**: Streamlit is the core framework for the web application user interface.
-   **Web Scraping**: Use `requests` for fetching web page content and `BeautifulSoup4` for parsing HTML.
-   **AI Backend**: Interact with an Ollama API endpoint for language model operations. The endpoint and model name are configured via environment variables in a `.env` file.
-   **Development Environment Setup**: Set up the local environment by running `make setup`. This command installs dependencies and creates a `.env` file from `.env.example` if it doesn't exist.

## Architectural Principles and File Structure

The project follows a clean, modular architecture enforcing a strict **Separation of Concerns (SoC)** and using **Dependency Injection** for testability.

-   **Core Principles**:
    -   **Separation of Concerns**: Logic is strictly divided: UI in `src/components`, business logic in `src/services`, and external API communication in `src/clients`.
    -   **Dependency Injection via Protocols**: Components must depend on abstract interfaces (`Protocol` classes from `src/protocols/`) rather than concrete implementations. This enables loose coupling and easy substitution with mocks.
-   **Directory Structure**:
    -   **`src/`**: Contains all primary application source code. For detailed implementation rules, see `@src/CLAUDE.md`.
        -   `components/`: Renders the UI and manages user interaction and application state (`st.session_state`).
        -   `services/`: Implements the core business logic, orchestrated by the components.
        -   `clients/`: Manages communication with external APIs.
        -   `protocols/`: Defines the abstract interfaces for services and clients.
    -   **`tests/`**: Contains all tests, structured by type. The `tests/unit-test` subdirectory mirrors the `src` directory structure. For detailed testing guidelines, see `@tests/CLAUDE.md`.
    -   **`dev/`**: Contains utilities for development and testing, primarily high-fidelity, protocol-compliant mocks. For rules on creating mocks, see `@dev/CLAUDE.md`.

## Coding Standards and Style Guide

Adhere strictly to the defined coding standards to maintain code quality and consistency.

-   **Formatter**: Always use Black to format all Python code. The command is `make format`.
-   **Linter**: Always use Ruff for linting and import sorting. The command is `make lint`.
-   **Ruff Configuration**: The configuration in `pyproject.toml` selects rules for Pyflakes (`F`), pycodestyle errors (`E`), and isort (`I`), while ignoring line length (`E501`) and unused variables (`F841`).
-   **Protocol Compliance**: Any new service or client in `src/` must have a corresponding interface defined in `src/protocols/`.

## Critical Business Logic and Invariants

-   **Application Flow**: The application is stateful and managed by `st.session_state`. The UI switches from the input page to the chat page by setting `st.session_state.show_chat` to `True`.
-   **URL Validation**: Before scraping, `ScrapingService.validate_url` must be called. It must reject non-`http/https` schemes and any hostname that resolves to a private, loopback, or reserved IP address.
-   **Content Scraping**: `ScrapingService.scrape` must remove non-content tags (`script`, `style`, `header`, `footer`, `nav`, `aside`) to isolate the main text.
-   **Summarization Prompt**: `SummarizationService` must use the specific Japanese prompt format requesting a "タイトル" (Title) and "要点" (Key Points).
-   **Chat State**: Chat history must be stored in `st.session_state.messages` as a list of dictionaries with "role" and "content" keys.

## Testing Strategy and Procedures

This project employs a multi-layered testing strategy, managed via the `Makefile`. For detailed guidelines, see `@tests/CLAUDE.md`.

-   **Framework**: Use `pytest` and `pytest-asyncio`.
-   **Execution**: Run the full suite with `make test` or specific suites with `make <target>` (e.g., `make unit-test`).
-   **Test Types**:
    1.  **Unit Tests**: Test components in isolation.
    2.  **Integration Tests**: Test interactions between internal components using mock dependencies from `dev/mocks`.
    3.  **Build Tests**: Verify the Streamlit server can start.
    4.  **E2E Tests**: Simulate user interaction in a browser using Selenium.

## CI Process

-   **Automation**: A GitHub Actions pipeline (`.github/workflows/ci-pipeline.yml`) runs on pushes and PRs to the `main` branch.
-   **Jobs**: The pipeline runs `make lint` and `make test`.
-   **Requirement**: All CI checks must pass before merging.

## Does Not Do

-   This application does not support non-`http/https` URLs.
-   It does not access local or private network addresses.
-   Chat history is not persisted between sessions.
-   The LLM model cannot be changed through the UI.