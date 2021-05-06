"""Class for processing pipeline."""
from typing import List
from io import BytesIO

import aiofiles

from src.consts.language import Language
from src.lockable import Lockable
from src.data_container import DataContainer
from src.data_persistence import DataPersistence
from src.storage import Storage
from src.recognizer import Recognizer
from src.notifier import Notifier
from src.describer import Describer
from src.rule import Rule

class Pipeline:
    """Class for processing pipeline."""

    class Processor(Lockable):
        """Class for processors to be piped up."""

        @property
        def lang(self):
            return self._lang

        @lang.setter
        def set_lang(self, lang: Language):
            self._lang = lang

        def __init__(self, recognizer: Recognizer, rules: DataPersistence[Rule], notifiers: DataContainer[Notifier], storage: Storage):
            self._lang = Language.EN_US
            self._recognizer = recognizer
            self._rules = rules
            self._notifiers = notifiers
            self._storage = storage

        async def process(self, input: aiofiles.threadpool.binary.AsyncBufferedIOBase or BytesIO or Recognizer.Result, key = None):
            """return output according to the input."""
            self._check_lock(key)

            if isinstance(input, (aiofiles.threadpool.binary.AsyncBufferedIOBase, BytesIO)):
                result = await self._recognizer.recognize(input)

                for rule in self._rules.get_all():
                    if not rule.time_range.operator(rule.time_range, 0):
                        continue

                    matched_findings = list(result.findings.filter(lambda result: rule.unkown.operator(rule.unkown, result.unkown)))
                    count = len(matched_findings)

                    if not rule.count.operator(rule.count, count):
                        continue

                    describer = Describer(self._lang)

                    describer.set_count(count)
                    describer.set_time_rage(0)
                    
                    if rule.unkown.operator == Rule.BooleanAttribute.BooleanComparisonOperator.EQUAL:
                        describer.set_unkown(rule.unkown)

                    for notifier in self._notifiers.get_all():
                        notifier.send(Notifier.Notification(Notifier.Notification.Level.WARNING, describer.to_string()))

            elif isinstance(input, Recognizer.Result):
                pass
            else:
                raise TypeError("Input must be a file or Recognizer.Result.")

    def __init(self, processors):
        for processor in processors:
            if not isinstance(processor, Pipeline.Processor):
                raise TypeError("Processor must be of type Pipeline.Processor.")

        self._processors = processors
    
    async def process(self, input):
        """Process the input through the pipeline."""

        middle_output = input

        for processor in self._processors:
            key = await processor.lock()
            middle_output = await processor.process(middle_output, key)
            processor.unlock(key)

        return middle_output
