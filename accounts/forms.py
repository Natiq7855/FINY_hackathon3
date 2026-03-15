from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from peerweave.mixins import BootstrapFormMixin


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=64, required=False)
    last_name = forms.CharField(max_length=64, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("skills", "interests", "goals", "timezone", "bio")
        widgets = {
            "skills": forms.TextInput(attrs={"placeholder": "python, django, design"}),
            "interests": forms.TextInput(attrs={"placeholder": "open-source, music, travel"}),
            "goals": forms.Textarea(attrs={"rows": 3}),
            "bio": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "skills": "Comma-separated list of your skills.",
            "interests": "Comma-separated list of your interests.",
        }
