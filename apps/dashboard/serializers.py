from rest_framework import serializers
from blog.models import Blog, Category, Tag, Comment
from accounts.models import User, Profile

class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.CharField(source='profile.avatar_url', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'avatar_url')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'icon_name')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class BlogSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False
    )
    tags = TagSerializer(many=True, read_only=True)
    reading_time = serializers.IntegerField(source='reading_time_minutes', read_only=True)

    class Meta:
        model = Blog
        fields = (
            'id', 'title', 'slug', 'featured_image', 'excerpt', 'content',
            'author', 'category', 'category_id', 'tags', 'status', 'view_count',
            'reading_time', 'is_featured', 'is_trending', 'seo_title', 'seo_description',
            'created_at', 'updated_at', 'published_at'
        )
        read_only_fields = ('id', 'slug', 'author', 'view_count', 'created_at', 'updated_at', 'published_at')
