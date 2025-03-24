from django.contrib import admin
from .models import Blogger, BlogPost, Comment, Like

# Register your models here.

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0

@admin.register(Blogger)
class BloggerAdmin(admin.ModelAdmin):
    list_display = ['user', 'bio', 'created_date']
    search_fields = ['user__username', 'bio']

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_date', 'is_protected', 'has_audio')
    list_filter = ('created_date', 'author', 'is_protected')
    search_fields = ('title', 'content', 'author__user__username')
    date_hierarchy = 'created_date'
    inlines = [CommentInline]

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_date')
    list_filter = ('created_date', 'author')
    search_fields = ('content', 'author__username', 'post__title')

    def truncated_content(self, obj):
        return obj.content[:75]
    truncated_content.short_description = 'Comment'

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_date')
    list_filter = ('created_date', 'user')
    search_fields = ('user__username', 'post__title')
