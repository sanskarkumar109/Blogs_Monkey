from django import forms
from django.core.exceptions import ValidationError
from .models import Blog, Comment, Category, Tag

class CommentForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white/60 dark:bg-slate-900/60 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 transition text-sm',
            'rows': 3,
            'placeholder': 'Share your insights or thoughts on this article...'
        }),
        max_length=1000
    )

    class Meta:
        model = Comment
        fields = ('content',)


class BlogForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full px-3.5 py-2.5 text-base font-medium rounded-md border border-[#e8e4de] dark:border-[#2e2c2a] bg-[#faf9f7] dark:bg-[#151413] text-[#1a1a1a] dark:text-[#faf9f7] focus:outline-none transition',
        'placeholder': 'Enter post title...'
    }))
    excerpt = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'w-full px-3.5 py-2 rounded-md border border-[#e8e4de] dark:border-[#2e2c2a] bg-[#faf9f7] dark:bg-[#151413] text-[#1a1a1a] dark:text-[#faf9f7] focus:outline-none transition text-xs',
        'rows': 2,
        'placeholder': 'Write a compelling short summary (max 400 chars)...'
    }))
    content = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'w-full px-3.5 py-2.5 rounded-md border border-[#e8e4de] dark:border-[#2e2c2a] bg-[#faf9f7] dark:bg-[#151413] text-[#1a1a1a] dark:text-[#faf9f7] focus:outline-none transition font-mono text-xs min-h-[350px]',
        'id': 'editor-textarea',
        'placeholder': 'Write your post content in Markdown or standard HTML...'
    }))
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="-- Select Category or Choose Custom --",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border border-[#e8e4de] dark:border-[#2e2c2a] bg-[#faf9f7] dark:bg-[#151413] text-[#1a1a1a] dark:text-[#faf9f7] text-xs focus:outline-none transition'
        })
    )
    custom_category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border border-[#e8e4de] dark:border-[#2e2c2a] bg-[#faf9f7] dark:bg-[#151413] text-[#1a1a1a] dark:text-[#faf9f7] text-xs focus:outline-none transition',
            'placeholder': 'Or type a custom category name...'
        }),
        help_text='If your category is not in the list, type it here to create it automatically.'
    )
    featured_image = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'block w-full text-xs text-[#6b6560] dark:text-[#9c9690] file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-medium file:bg-[#1a1a1a] file:text-white dark:file:bg-[#faf9f7] dark:file:text-[#1a1a1a] hover:file:opacity-90 transition'
    }))
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'w-full px-3 py-2 rounded-md border border-[#e8e4de] dark:border-[#2e2c2a] bg-[#faf9f7] dark:bg-[#151413] text-[#1a1a1a] dark:text-[#faf9f7] text-xs focus:outline-none transition'
        })
    )
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border border-[#e8e4de] dark:border-[#2e2c2a] bg-[#faf9f7] dark:bg-[#151413] text-[#1a1a1a] dark:text-[#faf9f7] text-xs focus:outline-none transition',
            'placeholder': 'e.g. django, python, webdev, saas'
        }),
        help_text='Type tags separated by commas.'
    )
    seo_title = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 rounded-md border border-[#e8e4de] dark:border-[#2e2c2a] bg-[#faf9f7] dark:bg-[#151413] text-[#1a1a1a] dark:text-[#faf9f7] text-xs focus:outline-none transition',
        'placeholder': 'SEO Meta Title'
    }))
    seo_description = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'w-full px-3 py-2 rounded-md border border-[#e8e4de] dark:border-[#2e2c2a] bg-[#faf9f7] dark:bg-[#151413] text-[#1a1a1a] dark:text-[#faf9f7] text-xs focus:outline-none transition',
        'placeholder': 'SEO Meta Description'
    }))

    class Meta:
        model = Blog
        fields = ('title', 'excerpt', 'content', 'category', 'custom_category', 'tags', 'tags_input', 'featured_image', 'seo_title', 'seo_description', 'canonical_url')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            tag_names = list(self.instance.tags.values_list('name', flat=True))
            if tag_names:
                self.initial['tags_input'] = ', '.join(tag_names)

    def clean_featured_image(self):
        image = self.cleaned_data.get('featured_image')
        if image and hasattr(image, 'size'):
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("Image file size must be under 5MB.")
            allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise ValidationError("Unsupported image format. Please upload JPEG, PNG, WEBP, or GIF.")
        return image

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Process Custom Category if provided
        custom_cat_name = self.cleaned_data.get('custom_category')
        if custom_cat_name and custom_cat_name.strip():
            clean_name = custom_cat_name.strip().title()
            category, _ = Category.objects.get_or_create(
                name=clean_name,
                defaults={'description': f'Articles about {clean_name}', 'icon_name': 'folder'}
            )
            instance.category = category

        if commit:
            instance.save()
            self._save_tags(instance)
        return instance

    def save_m2m(self):
        super().save_m2m()
        if self.instance:
            self._save_tags(self.instance)

    def _save_tags(self, instance):
        tags_raw = self.cleaned_data.get('tags_input')
        selected_tags = self.cleaned_data.get('tags')
        
        all_tags = []
        if selected_tags:
            all_tags.extend(list(selected_tags))

        if tags_raw:
            tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]
            for name in tag_names:
                tag_obj, _ = Tag.objects.get_or_create(
                    name=name,
                    defaults={'slug': name.lower().replace(' ', '-')}
                )
                if tag_obj not in all_tags:
                    all_tags.append(tag_obj)
                    
        if all_tags:
            instance.tags.set(all_tags)
        elif tags_raw is not None or selected_tags is not None:
            instance.tags.clear()
