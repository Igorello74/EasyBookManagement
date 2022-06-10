from django import forms


class ChoicesjsTextWidget(forms.widgets.Input):
    class Media:
        js = (
            'https://cdn.jsdelivr.net/npm/choices.js@9.0.1/public/assets/scripts/choices.min.js',
            'choices-js-manage.js'
        )
        css = {
            'all': (
                'https://cdn.jsdelivr.net/npm/choices.js@9.0.1/public/assets/styles/choices.min.css',
            )
        }

    def __init__(self, attrs={}):
        attrs['class'] = "choicesjs"

        super().__init__(attrs)

    def format_value(self, value):
        """Return selected values as a list."""
        return ','.join(value)

    def value_from_datadict(self, data, files, name):
        items = data[name].split(',')
        if items == ['']:
            return None

        return items
