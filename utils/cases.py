""" Russian grammatical cases and grammatical number

classes:
    Case - a enum with all Russian grammatical cases in singular
    and plural forms
    Cases - a dataclass to store a word in different cases

functions:
    nom(model), nom_pl(model), gen(model), gen_pl(model), dat(model),
    dat_pl(model), acc(model), acc_pl(model), ins(model), ins_pl(model),
    prep(model), prep_pl(model)

All these functions allow you to obtain a model's name in the according
grammatical case and grammatical number(singular and plural). A model
is expected to have an instance of the Cases dataclass named
`name_cases` with grammatical forms you need. If the model doesn't
declare the `name_cases` dataclass or if the dataclass doesn't have the
form you need, Model._meta.verbose_name or
Model._meta.verbose_name_plural are returned.
"""

from enum import Enum
from django.db import models
from dataclasses import InitVar, dataclass, fields


class Case(Enum):
    """Enum with all Russian grammatical cases"""

    NOM = "nom"  # nominative
    NOM_PL = "nom_pl"  # nominative plural
    GEN = "gen"  # genetive
    GEN_PL = "gen_pl"  # genetive plural
    DAT = "dat"  # dative
    DAT_PL = "dat_pl"  # dative plural
    ACC = "acc"  # accusative
    ACC_PL = "acc_pl"  # accusative plural
    INS = "ins"  # instrumental
    INS_PL = "ins_pl"  # instrumental plural
    PREP = "prep"  # prepositional
    PREP_PL = "prep_pl"  # prepositional plural


@dataclass
class Cases:
    """Dataclass to store word in different cases

    You can set all cases manually or pass a model's Meta class to the
    constructor, thus Meta.verbose_name and Meta.verbose_name_plural
    will be used to make up all unspecified cases.
    """

    nom: str = None
    nom_pl: str = None
    gen: str = None
    gen_pl: str = None
    dat: str = None
    dat_pl: str = None
    acc: str = None
    acc_pl: str = None
    ins: str = None
    ins_pl: str = None
    prep: str = None
    prep_pl: str = None

    meta: InitVar[type] = None

    def __post_init__(self, meta):
        if meta is None:
            return

        for f in fields(self):
            name = f.name
            if getattr(self, name, None) is None:
                if name.endswith("_pl"):
                    setattr(self, name, meta.verbose_name_plural)
                else:
                    setattr(self, name, meta.verbose_name)
        return


def _get_model_name_in_case(model: models.Model, case: Case):
    case = case.value
    plural = case.endswith("_pl")
    try:
        return getattr(model.name_cases, case)
    except AttributeError:
        if plural:
            return model._meta.verbose_name_plural
        else:
            return model._meta.verbose_name

def nom(model: models.Model):
    return _get_model_name_in_case(model, Case.NOM)
def nom_pl(model: models.Model):
    return _get_model_name_in_case(model, Case.NOM_PL)


def gen(model: models.Model):
    return _get_model_name_in_case(model, Case.GEN)
def gen_pl(model: models.Model):
    return _get_model_name_in_case(model, Case.GEN_PL)


def dat(model: models.Model):
    return _get_model_name_in_case(model, Case.DAT)
def dat_pl(model: models.Model):
    return _get_model_name_in_case(model, Case.DAT_PL)


def acc(model: models.Model):
    return _get_model_name_in_case(model, Case.ACC)
def acc_pl(model: models.Model):
    return _get_model_name_in_case(model, Case.ACC_PL)


def ins(model: models.Model):
    return _get_model_name_in_case(model, Case.INS)
def ins_pl(model: models.Model):
    return _get_model_name_in_case(model, Case.INS_PL)


def prep(model: models.Model):
    return _get_model_name_in_case(model, Case.PREP)
def prep_pl(model: models.Model):
    return _get_model_name_in_case(model, Case.PREP_PL)
