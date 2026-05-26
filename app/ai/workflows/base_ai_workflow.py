from abc import (
    ABC,
    abstractmethod,
)

from app.ai.ai_client import (
    AIClient
)


class BaseAIWorkflow(ABC):

    def __init__(self):

        self.client = (
            AIClient()
        )

    @abstractmethod
    def build_prompt(
        self,
        *args,
        **kwargs,
    ) -> str:

        pass

    @abstractmethod
    def execute(
        self,
        *args,
        **kwargs,
    ):

        pass