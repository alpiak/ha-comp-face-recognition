"""Classes for notifications."""
from enum import Enum

import twilio
import sine.properties

class Notifier:
    class Notification:
        class Level(Enum):
            INFO = "info"
            WARNING = "warning"
            ERROR = "error"

        @property
        def text(self):
            return self._text

        def __init__(self, level: Notifier.Notification.Level, text: str):
            self._level = level
            self._text = text

    def send(self, notification: Notifier.Notification):
        """Send a notification."""
        raise NotImplementedError()

class TwilioNotifier(Notifier):
    def __init__(self, credentials_path: str):
        with open(credentials_path, 'r') as file:
            properties = sine.properties.load(file)

            self._twilio = twilio.rest.Client(properties['sid'], properties['token'])
            self._number = properties['number']
            self._reciever_numbers = []

    def set_reciever_numbers(self, reciever_numbers: str):
        self._reciever_numbers = reciever_numbers

    def send(self, notification: Notifier.Notification):
        for number in self._reciever_numbers:
            self._twilio.messages.create(body = notification.text, from_ = self._number, to = number)
