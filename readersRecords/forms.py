from django import forms

from readersRecords.models import Reader


class ImportForm(forms.Form):
    file = forms.FileField(
        label="Файл", widget=forms.FileInput(attrs={"accept": ".xlsx,.csv"})
    )


class ReaderAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        g_num = self.initial.get("group_num")
        g_letter = self.initial.get("group_letter")
        self.initial["group"] = Reader.format_group(g_num, g_letter)

    group = forms.CharField(
        max_length=10,
        label="Класс",
        required=False,
        help_text='Можно писать как угодно: "11а", "11 а", "11-а", "11А"'
        ' — любой вариант будет нормализован до "11а"',
    )
    group_num = forms.IntegerField(widget=forms.HiddenInput, required=False)
    group_letter = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean(self):
        value = self.cleaned_data.get("group")
        g_num, g_letter = Reader._parse_group(value)
        return self.cleaned_data | {
            "group_num": g_num,
            "group_letter": g_letter,
        }
