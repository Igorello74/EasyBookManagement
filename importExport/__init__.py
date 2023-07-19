from collections import namedtuple


class InvalidDataError(RuntimeError):
    def __init__(self, invalid_objs: dict, *args):
        super().__init__(*args)
        self.invalid_objs = invalid_objs


class BadFileError(Exception):
    ...


VirtualField = namedtuple("VirtualField", ["setter", "real_fields"])
