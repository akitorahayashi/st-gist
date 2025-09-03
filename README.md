## Overview

This application is a web page summarization tool. By entering a URL, an AI analyzes and summarizes the content of the page, transforming it into a chatbot that you can ask questions about.

## Application Usage

1.  Enter the URL of the web page you want to summarize.
2.  Click the "要約を開始" (Start Summarization) button to begin the analysis.
3.  Once the summary is displayed, you can ask questions about the page's content in the chat interface that appears.

## Setup and Execution

1.  **Initial Setup**

    Run the setup command to install dependencies and create the `.env` file from the example.

    ```bash
    make setup
    ```

2.  **Environment Configuration**

    Modify the `.env` file with your local configuration, such as the Ollama API endpoint and model name.

    ```bash
    # .env
    OLLAMA_API_ENDPOINT=http://localhost:11434
    OLLAMA_MODEL=qwen3:0.6b
    ...
    ```

3.  **Launch Application**

    Start the Streamlit application using the development server.

    ```bash
    make run
    ```

## Development Workflow

-   **Code Formatting**

    To automatically format the code, run:

    ```bash
    make format
    ```

-   **Linter Execution**

    To check the code for linting issues, run:

    ```bash
    make lint
    ```

-   **Testing**

    To run the entire test suite (unit, integration, build, and E2E), use:

    ```bash
    make test
    ```

    You can also run specific test suites:

    ```bash
    make unit-test
    make intg-test
    make build-test
    make e2e-test
    ```
