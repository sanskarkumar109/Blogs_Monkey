from django.contrib.sitemaps import Sitemap
from blog.models import Blog, Category, Tag

class BlogSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Blog.published.all()

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Category.objects.all()


class TagSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Tag.objects.all()
