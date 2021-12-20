from django.contrib import admin

from .models import Group, Post, Comment, Follow


class PostAdmin(admin.ModelAdmin):
    """Кастомная админка для модели Post."""
    list_display = (
        'pk',
        'text',
        'pub_date',
        'image',
        'author',
        'group',
    )
    list_editable = ('group', 'image')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    """Кастомная админка для модели Group."""
    list_display = (
        'pk',
        'title',
        'slug',
        'description',

    )
    list_editable = ('title', 'slug',)
    list_filter = ('title',)
    search_fields = ('title',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    """Кастомная админка для модели Comment."""
    list_display = (
        'pk',
        'post',
        'author',
        'text',
        'created',
    )
    search_fields = ('author',)
    list_filter = ('created',)
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    """Кастомная админка для модели Follow."""
    list_display = (
        'user',
        'author',
    )
    list_filter = ('author', 'user',)
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follow, FollowAdmin)
