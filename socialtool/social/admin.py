from django.contrib import admin
from django.utils.safestring import mark_safe
from socialtool.loading import get_classes, get_model

SocialPostImageFilter, SocialPostStatusFilter = get_classes('social.filters',
('SocialPostImageFilter', 'SocialPostStatusFilter'))

# Register your models here.

def mark_deleted(modeladmin, request, queryset):
    queryset.update(deleted=True)
mark_deleted.short_description = 'Hide selected posts'

def mark_approved(modeladmin, request, queryset):
    queryset.update(approved=True)
mark_approved.short_description = 'Mark selected posts as approved'



class BaseAdmin(admin.ModelAdmin):

    class Media:
        js = ('js/tweet_admin.js', )
        css = {
            'all': ('css/adi051.css', )
        }


class SocialAdmin(BaseAdmin):
    search_fields = ('handle', 'content',)
    list_display = ('created_at', 'high_priority', 'get_handle', 'post_source', 'get_image', 'content', 'messages', 'notes', '_rudness_level')
    list_filter = ('account', 'search_term', 'high_priority', SocialPostStatusFilter, SocialPostImageFilter, 'created_at', 'entry_allowed', '_rudness_level')
    list_editable = ('notes', )

    list_per_page = 25

    actions = [mark_deleted, 'check_rudnesslevel_selected']

    fieldsets = (
        ('Post data', {
            'fields': ('created_at', 'handle', 'user_joined', 'followers',
                'post_url', 'post_source', ('account', 'search_term'), 'content',
                'image_url', 'uid', 'entry_allowed', 'disallowed_reason'),
        }),
        ('Make high priority', {
            'fields': ('high_priority', 'notes'),
        }),
        ('Sent data', {
            'classes': ('collapse', ),
            'fields': ('messaged_by', 'messaged_at', 'sent_id', 'sent_message', )
        }),
    )

    def get_image(self, obj):
        if obj.image_url:
            if 'twitpic' in obj.image_url:
                url = 'http://twitpic.com/show/thumb/{}'.format(obj.image_url.split('/')[-1])
            else:
                url = obj.image_url

            return mark_safe('<a href="{0}" target="_blank"><img src="{1}" width=100 /></a>'.format(obj.image_url, url))
        else:
            return "N/A"
    get_image.short_description = 'Original Image'

    def get_handle(self, obj):
        followers = '<p><em>({} Followers)</em></p>'.format(obj.followers) if obj.followers else ''
        return mark_safe("""
            <p><a href="http://{3}.com/{0}" target="_blank">{0}</a></p>
            <p><img src="{2}" /></p>
            {1}
        """.format(obj.handle.encode('utf-8'), followers, obj.profile_image, obj.account.type.lower()))
    get_handle.short_description = 'User\'s Handle'

    def messages(self, obj):
        return mark_safe("""
            <ul class="message-btns">
                <li><a class="btn btn-inverse ban-user">Ban User</a></li>
            </ul>
        """)
    messages.short_description = 'Post control'

    def save_model(self, request, obj, form, change):
        obj.save()

    def get_actions(self, request):
        actions = super(SocialAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_queryset(self, request):
        if request.user.is_superuser:
            return self.model.everything.get_query_set()

        return super(SocialAdmin, self).get_queryset(request)

    def check_rudnesslevel_selected(self, request, queryset):
        get_model('social', 'socialpost').everything.check_rudnesslevel(queryset)
    check_rudnesslevel_selected.short_description = "Check rudness for selected posts"

class MessageAdmin(BaseAdmin):
    list_display = ('account', 'type', 'copy')
    list_filter = ('account', 'type')

class ForbiddenWordAdmin(BaseAdmin):
    list_display = ('active', 'word', 'rudness_level')
    list_display_links = list()
    list_display_links.append('word')
    list_filter = ('active', 'rudness_level')
    list_editable = ('active', 'rudness_level')
    fields = ('active', 'word', 'rudness_level')

admin.site.register(get_model('social', 'socialpost'), SocialAdmin)
admin.site.register(get_model('social', 'searchterm'), BaseAdmin)
admin.site.register(get_model('social', 'banneduser'), BaseAdmin)
admin.site.register(get_model('social', 'message'), MessageAdmin)
admin.site.register(get_model('social', 'marketaccount'), BaseAdmin)
admin.site.register(get_model('social', 'trackedterms'), BaseAdmin)
admin.site.register(get_model('social', 'forbiddenword'), ForbiddenWordAdmin)
