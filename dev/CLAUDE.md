## CLAUDE.md Self-Modification Obligation

**Important**: This document governs the behavior of the claudecode agent itself. When changes are made to the codebase (adding dependencies, changing file structure, updating coding standards, etc.), claudecode is obligated to update this `CLAUDE.md` as part of the transaction to maintain consistency between the documentation and the implementation.

## Module Roles and Responsibilities

The `dev/` directory contains code and utilities that support the development and testing process but are not part of the production application. Its primary responsibility is to provide high-fidelity mock implementations of production components. These mocks enable predictable, isolated, and offline development and testing.

-   **`dev/mocks/`**: This subdirectory houses all mock objects. Each mock simulates a corresponding component from the `src/` directory, such as API clients and business logic services.

## Technology Stack and Environment

-   **Language**: Mocks are written in standard Python 3.12, consistent with the rest of the project.
-   **Asynchronous Simulation**: Use the `asyncio` library to simulate the asynchronous behavior of real components, such as API response streaming.

## Architectural Principles and File Structure

-   **Protocol Compliance (Mandatory)**: Every mock object that replaces a production component MUST implement the corresponding `Protocol` defined in `src/protocols/`. This is the most critical principle in this directory, as it ensures that mocks can be used as drop-in replacements for their real counterparts in tests and debug mode.
-   **Behavioral Fidelity**: Mocks must simulate the behavior of the real components as closely as possible. This includes simulating asynchronous streaming (`async for`) and returning data in the same format as the real component.
-   **Predictability**: Mocks must be deterministic. They must return predictable, hardcoded responses to facilitate reliable testing. Avoid randomness. For example, `MockScrapingService` returns specific content for a predefined set of URLs.
-   **File Naming**: Name mock implementation files with a `mock_` prefix, followed by the name of the component they are mocking (e.g., `mock_scraping_service.py`). Class names must have a `Mock` prefix (e.g., `MockScrapingService`).

## Coding Standards and Style Guide

-   **Formatting**: All code in this directory must be formatted with Black and Ruff by running `make format`.
-   **Clarity**: Mocks must be clearly documented with comments explaining what behavior they are simulating.
-   **Naming**: All mock classes must be prefixed with `Mock`, for example, `MockOllamaApiClient`.

## Usage in Development and Testing

-   **Debug Mode**: The mocks are used by `src/main.py` when the `DEBUG` environment variable is set to `true`. This allows the application to be run locally without requiring a connection to a live Ollama instance.
-   **Integration Testing**: The mock objects in this directory are the primary dependencies for the integration tests located in `tests/intg/`. They allow for testing the workflow and interaction of services without making external network calls.

## Does Not Do

-   This directory must not contain any production code.
-   Mocks must not contain any logic that makes external network calls or accesses external resources. They must be entirely self-contained.
-   This directory does not contain tests; it contains utilities that are *used by* tests. All test code belongs in the `tests/` directory.