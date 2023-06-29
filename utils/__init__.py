from collections import defaultdict


class ObjectFactory:
    def __init__(self):
        self._builders = {}

    def register(self, key, builder):
        self._builders[key] = builder

    def get(self, key, **kwargs):
        builder = self._builders.get(key)
        if not builder:
            raise ValueError(key)
        return builder(**kwargs)


def format_currency(val):
    if val is None:
        return 0
    val = float(val)
    if val.is_integer():
        val = int(val)
    return f"{val:,}".replace(",", " ")


class defaultdict_recursed(defaultdict):
    def __init__(self):
        super().__init__(defaultdict_recursed)

    def __getitem__(self, key):
        if key in {"items", "keys", "values"}:
            raise KeyError
        return super().__getitem__(key)
