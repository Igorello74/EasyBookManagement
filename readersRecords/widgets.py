from django import forms

class ChoicesjsMultipleWidget(forms.SelectMultiple):
    class Media:
        js = (
          'https://cdn.jsdelivr.net/npm/choices.js@9.0.1/public/assets/scripts/choices.min.js',
        )
        css = {
            'all':(
              'https://cdn.jsdelivr.net/npm/choices.js@9.0.1/public/assets/styles/choices.min.css',
            )
        }