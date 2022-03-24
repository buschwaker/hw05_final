from django.contrib import admin

from .models import Post, Group, Follow


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'created',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('created',)
    empty_value_display = '-пусто-'

# При регистрации модели Post источником конфигурации для неё назначаем
# класс PostAdmin


admin.site.register(Post, PostAdmin)


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'slug',
        'description',
    )
    search_fields = ('title',)
    empty_value_display = '-пусто-'


admin.site.register(Group, GroupAdmin)





admin.site.register(Follow)
