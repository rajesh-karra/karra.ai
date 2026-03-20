from django import forms
from django.utils import timezone
from django.utils.text import slugify

from .models import BlogPost


class BlogPostCreateForm(forms.ModelForm):
    publish_now = forms.BooleanField(required=False, initial=True, label="Publish immediately")

    class Meta:
        model = BlogPost
        fields = ["title", "summary", "body", "tags", "publish_now"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Post title"}),
            "summary": forms.Textarea(attrs={"rows": 3, "placeholder": "Short summary"}),
            "body": forms.Textarea(attrs={"rows": 18, "placeholder": "Write your post content"}),
            "tags": forms.TextInput(attrs={"placeholder": "[\"quantum\", \"ai\", \"qml\"]"}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Title is required.")
        return title

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            base_slug = slugify(instance.title) or "post"
            slug = base_slug
            index = 2
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{index}"
                index += 1
            instance.slug = slug

        if self.cleaned_data.get("publish_now"):
            instance.status = BlogPost.Status.PUBLISHED
            if not instance.published_at:
                instance.published_at = timezone.now()
        else:
            instance.status = BlogPost.Status.DRAFT

        if commit:
            instance.save()
        return instance
