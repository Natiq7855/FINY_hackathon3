"""Shared mixin to apply Bootstrap form-control classes to all Django form fields."""


class BootstrapFormMixin:
    """Add Bootstrap classes to all form field widgets automatically."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            css = widget.attrs.get("class", "")
            if widget.__class__.__name__ == "Select":
                widget.attrs["class"] = f"{css} form-select".strip()
            elif widget.__class__.__name__ == "CheckboxInput":
                widget.attrs["class"] = f"{css} form-check-input".strip()
            elif widget.__class__.__name__ == "Textarea":
                widget.attrs["class"] = f"{css} form-control".strip()
            else:
                widget.attrs["class"] = f"{css} form-control".strip()
