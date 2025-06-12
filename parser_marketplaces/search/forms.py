# forms.py

from django import forms

class SearchForm(forms.Form):
    query = forms.CharField(
        max_length=255,
        label="Введите товар для поиска:"
    )
    # limit = forms.IntegerField(
    #     label="Количество товаров",
    #     initial=20,
    #     min_value=1,
    #     max_value=100
    # )