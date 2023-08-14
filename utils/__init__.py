from collections import defaultdict
from dataclasses import asdict
from itertools import chain

from django.db import models
from django.forms import ModelForm


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


def compare_dicts_by_keys(d1: dict, d2: dict) -> dict:
    difference = {}

    for key, val1 in d1.items():
        if key not in d2:
            continue
        val2 = d2[key]
        if val1 != val2:
            difference[key] = (val1, val2)
    return difference


def model_to_dict(obj: models.Model) -> dict:
    opts = obj._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields):
        data[f.name] = f.value_from_object(obj)
    for f in opts.many_to_many:
        data[f.name] = sorted([i.pk for i in f.value_from_object(obj)])
    return data


def modelform_to_dict(form: ModelForm):
    opts = form._meta.model._meta
    data = {}
    cleaned_data = form.cleaned_data

    for f in chain(opts.concrete_fields, opts.private_fields):
        name = f.name
        if name in cleaned_data:
            if f.many_to_one or f.one_to_one:
                data[name] = cleaned_data[name].pk
            else:
                data[name] = cleaned_data[name]

    for f in opts.many_to_many:
        if f.name in cleaned_data:
            data[f.name] = sorted([i.pk for i in cleaned_data[f.name]])
    return data


def _dict_factory(items):
    return dict((k, v) for k, v in items if v is not None)


def dataclass_to_dict(obj):
    """Transform a dataclass to dict

    Items with the value of None are skipped.
    """
    return asdict(obj, dict_factory=_dict_factory)
