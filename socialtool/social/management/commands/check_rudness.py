from django.core.management.base import BaseCommand
from socialtool.loading import get_model

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        SocialPost = get_model('social', 'socialpost')
        SocialPost.everything.check_rudnesslevel(SocialPost.everything.all())
