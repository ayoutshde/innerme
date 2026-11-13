from django import forms
from django.utils.timezone import localdate
from .data import TAGS

class EntryForm(forms.Form):
    mood = forms.IntegerField(min_value=1,max_value=5,error_messages={"required":"Мэдрэмжээ сонгоорой."})
    tags = forms.MultipleChoiceField(choices=[(t,t) for t in TAGS],required=False)
    note = forms.CharField(max_length=800,required=False,widget=forms.Textarea(attrs={
        "rows":4,"placeholder":"Юу санаанд чинь үлдэв? Нэг өгүүлбэр ч байж болно."
    }))
    day = forms.DateField(widget=forms.DateInput(format="%Y-%m-%d", attrs={"type":"date"}))

    def clean_day(self):
        day = self.cleaned_data["day"]
        if day > localdate():
            raise forms.ValidationError("Ирээдүйн огноо сонгох боломжгүй.")
        return day
