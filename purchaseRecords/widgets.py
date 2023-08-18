from django import forms


class DateInput(forms.TextInput):
    input_type = "date"
