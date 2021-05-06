"""Class to describe the persons found by recognizer."""
from src.utils import milliseconds_to_string

from src.consts.language import Language

class Describer:
    """Class to describe the persons found by recognizer."""

    class Attribute:
        """Attribute of the describer"""

        @property
        def value(self):
            return self._value

        def __init__(self, value):
            self._value = value

    class BooleanAttribute(Attribute):
        """Attribute of boolean type."""

        def __init__(self, value: bool):
            super().__init__(value)

    class IntegerAttribute(Attribute):
        """Attribute of integer type."""

        def __init__(self, value: int):
            super().__init__(value)

    @property
    def time_range(self):
        return self._time_range

    @time_range.setter
    def set_time_rage(self, time_range: Describer.IntegerAttribute):
        self._time_range = time_range

    @property
    def count(self):
        return self._count

    @count.setter
    def set_count(self, count):
        if not isinstance(count, Describer.IntegerAttribute):
            raise TypeError

        self._count = count

    @property
    def unkown(self):
        return self._unkown

    @unkown.setter
    def set_unkown(self, unkown):
        if not isinstance(unkown, Describer.BooleanAttribute):
            raise TypeError

        self._unkown = unkown
    
    def __init__(self, lang = Language.EN_US):
        self._time_range = None # In milliseconds
        self._count = None
        self._unkown = None
        self._lang: Language = lang

    def to_string(self):
        if self._lang == Language.EN_US or self._lang == Language.EN:
            return '{} {} persons has been captured in {}.'.format(self._count.value, self._get_unkown_string(), milliseconds_to_string(self._time_range, self._lang))
        elif self._lang == Language.ZH_CN or self._lang == Language.ZH:
            return '{}内拍摄到{}个{}人。'.format(milliseconds_to_string(self._time_range, self._lang), self._count.value, self._get_unkown_string())

    def _get_unkown_string(self):
        mapping = None

        if self._lang == Language.EN_US or self._lang == Language.EN:
            mapping = {
                True: 'known',
                False: 'unkown',
                None: 'known or unkown',
            }
        if self._lang == Language.ZH_CN or self._lang == Language.ZH:
            mapping = {
                True: '已知的',
                False: '未知的',
                None: '已知或未知的',
            }
        else:
            mapping = {
                True: 'known',
                False: 'unkown',
                None: 'known or unkown',
            }

        return mapping[self._unkown.value]
