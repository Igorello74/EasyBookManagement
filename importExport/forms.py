from django import forms


class ImportForm(forms.Form):
    file = forms.FileField(
        label="Файл", widget=forms.FileInput(attrs={"accept": ".xlsx,.csv"})
    )
