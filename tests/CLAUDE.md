## CLAUDE.md Self-Modification Obligation

**Important**: This document governs the behavior of the claudecode agent itself. When changes are made to the codebase (adding dependencies, changing file structure, updating coding standards, etc.), claudecode is obligated to update this `CLAUDE.md` as part of the transaction to maintain consistency between the documentation and the implementation.

## Module Roles and Responsibilities

This directory, `tests/`, contains the complete test suite for the application. Its primary role is to ensure the correctness, reliability, and stability of the application through a multi-layered testing strategy. It is responsible for verifying individual components in isolation, the integrations between them, the application's build integrity, and the end-to-end user experience.

## Technology Stack and Environment

-   **Testing Framework**: Use `pytest` as the sole framework for writing and running tests.
-   **Asynchronous Testing**: Use `pytest-asyncio` to test `async` functions, particularly in services and clients. The `asyncio_mode` is set to `auto`.
-   **End-to-End Testing**: Use `selenium` for browser automation in end-to-end tests.
-   **Mocking**: Use Python's built-in `unittest.mock` for unit tests. For integration tests, use the pre-built mock services and clients located in the `dev/mocks/` directory.

## Architectural Principles and File Structure

-   **Test Directory Structure**: The `tests/` directory must be organized into four subdirectories, each corresponding to a specific layer of the testing strategy:
    -   `build/`: For tests that verify the application can be built and started.
    -   `e2e/`: For end-to-end browser-based tests.
    -   `intg/`: For integration tests between internal application components.
    -   `unit-test/`: For unit tests of individual modules, functions, and classes.
-   **Unit Test Mirroring**: The directory structure within `tests/unit-test/` must mirror the structure of the `src/` directory. For example, tests for `src/services/scraping_service.py` must be located in `tests/unit-test/services/test_scraping_service.py`.
-   **File Naming**: All test files must be prefixed with `test_`.

## Coding Standards and Style Guide

-   **Code Formatting**: All test code must be formatted with Black and Ruff by running `make format`.
-   **Test Organization**: Organize related tests into classes (e.g., `TestScrapingService`). Use `setup_method` for common test setup within a class.
-   **Method Naming**: Test method names must be descriptive and clearly state the condition being tested (e.g., `test_validate_url_invalid_scheme`).
-   **Assertions**: Use clear and direct `assert` statements. Avoid complex logic within an assertion.

## Testing Strategy and Procedures

Adhere to the following four-tiered testing strategy. All new code must be accompanied by appropriate tests.

1.  **Unit Tests (`unit-test`)**
    -   **Purpose**: To test a single function or class in complete isolation.
    -   **Rule**: Mock all dependencies, including other services, clients, and Streamlit's `session_state`.
    -   **Command**: `make unit-test`

2.  **Integration Tests (`intg`)**
    -   **Purpose**: To test the interaction between internal application components (e.g., how the `SummarizationService` uses the `OllamaApiClient`).
    -   **Rule**: Use the mock clients and services from the `dev/mocks` directory to simulate external dependencies. Never make live network calls.
    -   **Command**: `make intg-test`

3.  **Build Tests (`build`)**
    -   **Purpose**: To verify that the Streamlit application server can start successfully without import errors or immediate crashes.
    -   **Rule**: These tests should be simple "smoke tests" that start the server and check for a successful HTTP response.
    -   **Command**: `make build-test`

4.  **End-to-End Tests (`e2e`)**
    -   **Purpose**: To simulate a real user interacting with the application in a headless browser to catch UI and workflow issues.
    -   **Rule**: These tests launch the full application and use Selenium to perform actions like loading the page and checking for the absence of error messages.
    -   **Command**: `make e2e-test`

To run the entire suite, use the command `make test`.

## CI Process

-   All test suites are executed automatically via GitHub Actions for every push and pull request to the `main` branch.
-   The workflow runs each test suite in a separate, parallel job to ensure clarity and speed.
-   Passing all tests is a mandatory requirement for merging code.

## Does Not Do

-   Tests must never make calls to live external APIs (like the real Ollama endpoint). Always use the mock clients from `dev/mocks`.
-   Unit tests must not have dependencies on other internal services; these must be mocked using `unittest.mock`.
-   Tests do not write or modify files outside of the `tests` directory and its artifacts (e.g., `.pytest_cache`).