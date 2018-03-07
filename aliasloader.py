import json


class AliasLoader:
    def get_dict(self, content):
        raw_aliases = json.loads(content.decode('UTF-8'))
        aliases = {}
        for pattern in raw_aliases.keys():
            aliases[pattern] = lambda x, p=pattern: raw_aliases[p][x] if\
                x in raw_aliases[p].keys() else raw_aliases[p]["default"]
        return aliases
