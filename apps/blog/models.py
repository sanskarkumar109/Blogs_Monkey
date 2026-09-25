import math
import nh3
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse

class BlogStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PENDING_REVIEW = 'pending_review', 'Pending Review'
    PUBLISHED = 'published', 'Published'
    REJECTED = 'rejected', 'Rejected'
    ARCHIVED = 'archived', 'Archived'


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    description = models.TextField(blank=True, max_length=300)
    icon_name = models.CharField(max_length=50, default='folder', help_text='Feather/Heroicon name')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:category_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:tag_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return f"#{self.name}"


class PublishedBlogManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=BlogStatus.PUBLISHED)


class Blog(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=250, unique=True, db_index=True)
    featured_image = models.ImageField(upload_to='blogs/%Y/%m/', blank=True, null=True)
    excerpt = models.TextField(max_length=400, help_text='Short summary for listing preview')
    content = models.TextField(help_text='Rich content in HTML or Markdown')
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blogs'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blogs'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='blogs')
    
    status = models.CharField(
        max_length=20,
        choices=BlogStatus.choices,
        default=BlogStatus.DRAFT,
        db_index=True
    )
    rejection_reason = models.TextField(blank=True, help_text='Feedback provided by admin if rejected')
    
    is_featured = models.BooleanField(default=False, db_index=True)
    is_trending = models.BooleanField(default=False, db_index=True)
    view_count = models.PositiveIntegerField(default=0)
    reading_time_minutes = models.PositiveIntegerField(default=1)
    
    # SEO fields
    seo_title = models.CharField(max_length=70, blank=True, help_text='SEO Meta Title (max 70 chars)')
    seo_description = models.CharField(max_length=160, blank=True, help_text='SEO Meta Description (max 160 chars)')
    canonical_url = models.URLField(blank=True, help_text='Custom Canonical URL if cross-posted')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = models.Manager() # Default manager
    published = PublishedBlogManager() # Custom manager for published blogs

    class Meta:
        verbose_name = 'Blog'
        verbose_name_plural = 'Blogs'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['is_featured', 'status']),
            models.Index(fields=['is_trending', 'status']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:blog_detail', kwargs={'slug': self.slug})

    def calculate_reading_time(self) -> int:
        words = len(self.content.split())
        minutes = math.ceil(words / 200) # Average 200 wpm
        return max(1, minutes)

    def save(self, *args, **kwargs):
        # Generate slug if empty
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Blog.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            
        # Calculate reading time
        self.reading_time_minutes = self.calculate_reading_time()
        
        # Sanitize HTML content against XSS attacks using nh3
        if self.content:
            # Allow common rich text tags
            allowed_tags = {
                'a', 'b', 'blockquote', 'code', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'i', 'img', 'li', 'ol', 'p', 'pre', 'strong', 'ul', 'span', 'div', 'br', 'hr',
                'table', 'thead', 'tbody', 'tr', 'th', 'td', 'mark'
            }
            allowed_attrs = {
                'a': {'href', 'title', 'target', 'rel'},
                'img': {'src', 'alt', 'title', 'width', 'height', 'class'},
                '*': {'class', 'style', 'id'}
            }
            self.content = nh3.clean(self.content, tags=allowed_tags, attributes=allowed_attrs, link_rel=None)

        # Set published timestamp if publishing for first time
        if self.status == BlogStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    @property
    def meta_title(self) -> str:
        return self.seo_title or self.title

    @property
    def meta_description(self) -> str:
        return self.seo_description or (self.excerpt[:157] + '...' if len(self.excerpt) > 160 else self.excerpt)


class Comment(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=1000)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.blog.title}"


class Like(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blog', 'user')

    def __str__(self):
        return f"{self.user.username} liked {self.blog.title}"


class Bookmark(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blog', 'user')

    def __str__(self):
        return f"{self.user.username} bookmarked {self.blog.title}"
