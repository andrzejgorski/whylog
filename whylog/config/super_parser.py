import re
from abc import ABCMeta, abstractmethod

import six

from whylog.converters import CONVERTION_MAPPING, STRING


@six.add_metaclass(ABCMeta)
class AbstractSuperParser(object):
    @abstractmethod
    def get_ordered_groups(self, line):
        pass


class RegexSuperParser(AbstractSuperParser):
    NO_MATCH = []

    def __init__(self, regex_str, group_order, convertions):
        self.regex = re.compile(regex_str)
        self.group_order = group_order
        self.convertions = convertions

    def serialize(self):
        return {
            'regex_str': self.regex.pattern,
            'group_order': self.group_order,
            'convertions': self.convertions
        }

    def __eq__(self, other):
        return self.serialize() == other.serialize()

    def get_ordered_groups(self, line):
        match = self.regex.match(line)
        if not match:
            return self.NO_MATCH
        groups = match.groups()
        result = []
        for group_nr in self.group_order:
            convertion_type = self.convertions.get(group_nr)
            group_to_convert = groups[group_nr - 1]
            if convertion_type is None:
                result.append((STRING, group_to_convert))
                continue
            converter = CONVERTION_MAPPING[convertion_type]
            result.append((convertion_type, converter.convert(group_to_convert)))
        return result


@six.add_metaclass(ABCMeta)
class AbstractSuperParserFactory(object):
    @classmethod
    @abstractmethod
    def from_dao(cls, serialized):
        pass


class RegexSuperParserFactory(AbstractSuperParserFactory):
    @classmethod
    def from_dao(cls, serialized):
        return RegexSuperParser(**serialized)
