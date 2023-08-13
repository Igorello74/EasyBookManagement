from django.contrib import admin

from readersRecords.models import Reader


class GroupFilter(admin.SimpleListFilter):
    title = "класс"
    template = "readersRecords/reader-admin-filter.html"
    parameter_name = "group"
    QUERY_SEPARATOR = "~"

    def lookups(self, request, model_admin):
        result = list(
            Reader.objects.values_list("group_num", "group_letter")
            .order_by("group_num", "group_letter")
            .distinct()
        )

        groups = {}
        for num, letter in result:
            groups.setdefault(num, []).append(letter)
        self.groups = groups

        return [...]

    def queryset(self, request, queryset):
        if self.value() is None:
            v = None
        else:
            v = str(self.value()).split(self.QUERY_SEPARATOR)
        match v:
            case ["None"]:
                return queryset.filter(group_num=None)
            case ["None", letter]:
                return queryset.filter(group_num=None, group_letter=letter)
            case [num]:
                return queryset.filter(group_num=num)
            case [num, letter]:
                return queryset.filter(group_num=num, group_letter=letter)
            case _:
                return queryset

    def choices(self, changelist):
        yield {
            "selected": self.value() is None,
            "query_string": changelist.get_query_string(remove=[self.parameter_name]),
            "display": "Все",
        }
        for num, letters_list in self.groups.items():
            sub_choices = []
            for letter in letters_list:
                lookup = f"{num}{self.QUERY_SEPARATOR}{letter}"
                sub_choices.append(
                    {
                        "display": Reader.format_group(num, letter),
                        "query_string": changelist.get_query_string(
                            {self.parameter_name: lookup}
                        ),
                        "selected": self.value() == lookup,
                    }
                )

            lookup = str(num)
            yield {
                "selected": self.value() == str(lookup),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": "Не указан" if num is None else f"{num} классы",
                "sub_choices": sub_choices,
            }
