import re


class AliasLoader:
    def __init__(self, alias_extracter):
        self.__extract_alias = alias_extracter

    def get_alias_substitution_list(self, lines):
        alias_patterns_and_replacements = []
        for line in lines:
            match = self.__extract_alias(line)
            if match is None:
                continue
            alias_patterns_and_replacements.append((re.compile('%{}%'.format(
                match.group(1))),
                                                    match.group(2)))
        return alias_patterns_and_replacements
