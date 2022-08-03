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