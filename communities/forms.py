from django import forms
from .models import Community
from peerweave.mixins import BootstrapFormMixin


class CommunityForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Community
        fields = ("name", "description")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
