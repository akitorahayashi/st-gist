from src.protocols.models.summarization_model_protocol import SummarizationModelProtocol


class MockSummarizationModel(SummarizationModelProtocol):
    """
    Mock summarization model for testing and development.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client  # Not used in mock but kept for compatibility

    pass
