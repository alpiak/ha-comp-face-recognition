"""Class for rules to checked by recognizer."""
from enum import Enum

from src.describer import Describer

class Rule(Describer):
    """Class for rules to checked by recognizer."""

    class Attribute(Describer.Attribute):
        """Attribute of the describer"""

        @property
        def operator(self):
            return self._operator

        def __init__(self, value, operator):
            super().__init__(value)

            self._operator = operator

    class BooleanAttribute(Rule.Attribute, Describer.BooleanAttribute):
        """Attribute of boolean type."""

        class BooleanComparisonOperator(Enum):
            EQUAL = lambda attribute, value: value == attribute._value
            EQUAL_OR_NOT_EQUAL = lambda _: True

        def __init__(self, value, operator):
            if not isinstance(operator, Rule.BooleanAttribute.BooleanComparisonOperator):
                raise TypeError

            Rule.Attribute.__init__(self, value, operator)
            Describer.BooleanAttribute.__init__(self, value)

    class IntegerAttribute(Rule.Attribute, Describer.IntegerAttribute):
        """Attribute of integer type."""

        class IntegerComparisonOperator(Enum):
            EQUAL = lambda attribute, value: value == attribute._value
            GREATER_THAN = lambda attribute, value: value > attribute._value
            GREATER_THAN_AND_EQUAL = lambda attribute, value: value >= attribute._value
            LESS_THAN = lambda attribute, value: value < attribute._value
            LESS_THAN_AND_EQUAL = lambda attribute, value: value <= attribute._value

        def __init__(self, value, operator):
            if not isinstance(operator, Rule.IntegerAttribute.IntegerComparisonOperator):
                raise TypeError

            Rule.Attribute.__init__(self, value, operator)
            Describer.IntegerAttribute.__init__(self, value)

    @property
    def time_range(self):
        return super().time_range

    @time_range.setter
    def set_time_rage(self, time_range):
        if not isinstance(time_range, Rule.IntegerAttribute):
            raise TypeError

        self._time_range = time_range

    @property
    def count(self):
        return super().count

    @count.setter
    def set_count(self, count):
        if not isinstance(count, Rule.IntegerAttribute):
            raise TypeError

        self._count = count

    @property
    def unkown(self):
        return super().unkown

    @unkown.setter
    def set_unkown(self, unkown):
        if not isinstance(unkown, Rule.BooleanAttribute):
            raise TypeError

        self._unkown = unkown
