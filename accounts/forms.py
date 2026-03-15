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
        fields = ("skills", "interests", "goals", "timezone", "bio", "intent", "communication_style")
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


# ── Cognitive Onboarding Step Forms ──────────────────────────────────

class OnboardingStep1Form(BootstrapFormMixin, forms.Form):
    """Step 1: User intent."""
    intent = forms.ChoiceField(
        choices=Profile.INTENT_CHOICES,
        widget=forms.RadioSelect(attrs={"class": ""}),
        label="What brings you here?",
    )


class OnboardingStep2Form(BootstrapFormMixin, forms.Form):
    """Step 2: Top interests (multi-select)."""
    INTEREST_OPTIONS = [
        ("python", "Python"), ("javascript", "JavaScript"), ("design", "Design"),
        ("data-science", "Data Science"), ("machine-learning", "Machine Learning"),
        ("web-dev", "Web Development"), ("mobile", "Mobile Dev"), ("devops", "DevOps"),
        ("marketing", "Marketing"), ("content", "Content Creation"),
        ("open-source", "Open Source"), ("ux", "UX/UI"),
    ]
    interests = forms.MultipleChoiceField(
        choices=INTEREST_OPTIONS,
        widget=forms.CheckboxSelectMultiple(attrs={"class": ""}),
        label="Select your top interests",
    )


class OnboardingStep3Form(BootstrapFormMixin, forms.Form):
    """Step 3: Communication style."""
    communication_style = forms.ChoiceField(
        choices=Profile.COMM_STYLE_CHOICES,
        widget=forms.RadioSelect(attrs={"class": ""}),
        label="How do you prefer to communicate?",
    )
