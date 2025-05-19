from abc import ABC, abstractmethod

class EmailConnector(ABC):
    """
    Abstract base class for email connectors.
    Defines a common interface for connecting to, reading from,
    and disconnecting from email services.
    """

    @abstractmethod
    def connect(self):
        """
        Establishes a connection to the email server.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Closes the connection to the email server.
        """
        pass

    @abstractmethod
    def read_emails(self, criteria="UNSEEN"):
        """
        Reads emails from the inbox based on specified criteria.

        Args:
            criteria (str): Search criteria for emails (e.g., "UNSEEN", "ALL").

        Returns:
            list: A list of email objects or dictionaries containing email data.
        """
        pass

    # Future potential methods:
    # @abstractmethod
    # def send_email(self, to_address, subject, body):
    #     pass
    #
    # @abstractmethod
    # def mark_as_read(self, email_id):
    #     pass
    #
    # @abstractmethod
    # def move_email(self, email_id, folder_name):
    #     pass 