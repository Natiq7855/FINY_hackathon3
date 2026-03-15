from django import forms
from .models import HelpRequest, HelpResponse
from peerweave.mixins import BootstrapFormMixin


class HelpRequestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = HelpRequest
        fields = ("title", "description", "tags")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "tags": forms.TextInput(attrs={"placeholder": "python, design, marketing"}),
        }
        help_texts = {
            "tags": "Comma-separated tags for expert matching.",
        }


class HelpResponseForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = HelpResponse
        fields = ("message",)
        widgets = {
            "message": forms.Textarea(attrs={"rows": 3, "placeholder": "Share your expertise..."}),
        }
