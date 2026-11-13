import re
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
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


IDENTIFIER_ERROR = "Имэйл хаяг эсвэл утасны дугаараа зөв оруулна уу."

def normalize_identifier(raw):
    """Имэйл эсвэл утасны дугаарыг нэг хэлбэрт оруулна. (нэр, "email" | "phone") буцаана."""
    value = (raw or "").strip()
    if "@" in value:
        email = value.lower()
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError(IDENTIFIER_ERROR)
        if len(email) > 150:
            raise ValidationError(IDENTIFIER_ERROR)
        return email, "email"
    compact = re.sub(r"[\s\-().]", "", value)
    if re.fullmatch(r"\d{8}", compact):                  # 99112233
        return "+976" + compact, "phone"
    if re.fullmatch(r"976\d{8}", compact):               # 97699112233
        return "+" + compact, "phone"
    if re.fullmatch(r"\+\d{9,15}", compact):             # +97699112233, +821012345678
        return compact, "phone"
    raise ValidationError(IDENTIFIER_ERROR)

class SignupForm(forms.Form):
    identifier = forms.CharField(max_length=150, error_messages={"required": "Имэйл эсвэл утасны дугаараа оруулна уу."})
    password1 = forms.CharField(widget=forms.PasswordInput, error_messages={"required": "Нууц үгээ оруулна уу."})
    password2 = forms.CharField(widget=forms.PasswordInput, error_messages={"required": "Нууц үгээ давтан оруулна уу."})

    def clean_identifier(self):
        username, kind = normalize_identifier(self.cleaned_data["identifier"])
        if get_user_model().objects.filter(username=username).exists():
            raise ValidationError("Энэ имэйл эсвэл утасны дугаараар бүртгэл үүссэн байна. Нэвтэрнэ үү.")
        self.kind = kind
        return username

    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2:
            if p1 != p2:
                self.add_error("password2", "Нууц үг таарахгүй байна.")
            else:
                try:
                    validate_password(p1)
                except ValidationError as e:
                    self.add_error("password1", e)
        return data

    def save(self):
        username = self.cleaned_data["identifier"]
        email = username if self.kind == "email" else ""
        return get_user_model().objects.create_user(username=username, email=email,
                                                    password=self.cleaned_data["password1"])

class LoginForm(forms.Form):
    identifier = forms.CharField(max_length=150, error_messages={"required": "Имэйл эсвэл утасны дугаараа оруулна уу."})
    password = forms.CharField(widget=forms.PasswordInput, error_messages={"required": "Нууц үгээ оруулна уу."})

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None

    def clean(self):
        data = super().clean()
        if data.get("identifier") and data.get("password"):
            try:
                username, _ = normalize_identifier(data["identifier"])
            except ValidationError:
                username = None
            self.user = authenticate(self.request, username=username, password=data["password"]) if username else None
            if self.user is None:
                raise ValidationError("Имэйл/утасны дугаар эсвэл нууц үг буруу байна.")
        return data
