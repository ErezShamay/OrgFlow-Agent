from abc import ABC
from abc import abstractmethod


class BaseEmailProvider(ABC):

    @abstractmethod
    def get_unread_messages(self):
        pass

    @abstractmethod
    def send_email(
        self,
        to,
        subject,
        body
    ):
        pass

    @abstractmethod
    def download_attachments(
        self,
        message_id
    ):
        pass