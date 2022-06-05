from django import forms

class ChoicesjsMultipleWidget(forms.SelectMultiple):
    class Media:
        js = (
          'https://cdn.jsdelivr.net/npm/choices.js@9.0.1/public/assets/scripts/choices.min.js',
          'choices-js-manage.js'
        )
        css = {
            'all':(
              'https://cdn.jsdelivr.net/npm/choices.js@9.0.1/public/assets/styles/choices.min.css',
            )
        }

    def __init__(self, attrs=None, choices=()):
        attrs = attrs or {}

        attrs['choicesjs'] = "choicesjs"

        super().__init__(attrs, choices)