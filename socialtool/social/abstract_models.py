from django.db import models
from django.contrib.auth.models import User
from socialtool.loading import get_classes, get_model
from django.conf import settings

SocialPostManager, AllSocialPostManager = get_classes('social.managers', ('SocialPostManager', 'AllSocialPostManager'))


class AbstractMarketAccount(models.Model):
    """
        This model allows us to actual query the social networks and interact
        with them.
    """
    ACCOUNT_CHOICES = (
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
    )

    type = models.CharField(max_length=50, unique=True, choices=ACCOUNT_CHOICES)
    handle = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    # Optionally associate with a particular user for filtering/ACL
    user = models.ForeignKey(User, blank=True, null=True)

    # Instagram
    client_id = models.CharField(max_length=100, blank=True, null=True)
    client_secret = models.CharField(max_length=100, blank=True, null=True)

    # Twitter
    consumer_secret = models.CharField(max_length=100, blank=True, null=True)
    consumer_key = models.CharField(max_length=100, blank=True, null=True)
    access_token_secret = models.CharField(max_length=100, blank=True, null=True)
    access_token_key = models.CharField(max_length=100, blank=True, null=True)

    def __unicode__(self):
        return u'{0} ({1})'.format(self.handle, self.type)

    class Meta:
        abstract = True


class AbstractMessage(models.Model):
    MESSAGE_TYPES = (
        ('f', 'Fail'),
        ('s', 'Success'),
    )

    copy = models.CharField(max_length=140)
    account = models.ForeignKey('social.MarketAccount')
    type = models.CharField(max_length=1, choices=MESSAGE_TYPES)

    def __unicode__(self):
        return u'{0} ({1}...)'.format(self.account, self.copy[:30])

    class Meta:
        abstract = True


class AbstractTrackedTerms(models.Model):
    """
        Associate a particular user with various search terms. We can then
        filter on these to give a particular feed
    """
    user = models.ForeignKey(User, unique=True)
    terms = models.ManyToManyField('social.SearchTerm')

    def __unicode__(self):
        return u'{} ({})'.format(self.user, ','.join(self.terms.values_list('term', flat=True)))

    class Meta:
	abstract = True
        verbose_name_plural = 'Tracked Terms'


class AbstractBannedUser(models.Model):
    handle = models.CharField(max_length=100, unique=True)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.handle

    class Meta:
        abstract = True

class AbstractForbiddenWord(models.Model):
    """
        Social Post's content is search against these words.
        A rudness level is then given to it according to the words that have been found and their level.
    """
    active = models.BooleanField(default=True)
    word = models.SlugField()
    rudness_level = models.IntegerField()
    
    def __unicode__(self):
        return self.word

    class Meta:
        abstract = True

class AbstractSearchTerm(models.Model):
    active = models.BooleanField(default=False)
    term = models.CharField(max_length=100)

    def __unicode__(self):
        return u'{0} ({1})'.format(self.term, self.active)

    class Meta:
        abstract = True


class AbstractSocialPost(models.Model):
    created_at = models.DateTimeField()
    created_at.verbose_name = 'Post date'
    uid = models.CharField(max_length=100, unique=True)
    post_url = models.URLField(max_length=255, null=True, blank=True)
    handle = models.CharField(max_length=100)
    post_source = models.CharField(max_length=100, blank=True, null=True)
    followers = models.IntegerField(blank=True, null=True)
    user_joined = models.DateTimeField(blank=True, null=True)
    profile_image = models.URLField(max_length=255, blank=True, null=True)
    content = models.CharField(max_length=1000)
    approved = models.BooleanField(default=False)
    high_priority = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    entry_allowed = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    notes.verbose_name = 'internal notes'
    account = models.ForeignKey('social.MarketAccount', blank=True, null=True)
    account.verbose_name = 'Social source'
    search_term = models.ForeignKey('social.SearchTerm')
    content.verbose_name = 'user\'s post'
    image_url = models.URLField(max_length=255, blank=True, null=True)
    messaged = models.BooleanField(default=False)
    messaged.verbose_name = 'Post status'
    sent_message = models.CharField(max_length=140, blank=True, null=True)
    # note the FKs: https://docs.djangoproject.com/en/dev/topics/db/models/#be-careful-with-related-name
    messaged_by = models.ForeignKey(User, related_name='%(class)s_messenger', blank=True, null=True)
    messaged_at = models.DateTimeField(blank=True, null=True)
    sent_id = models.CharField(max_length=100, blank=True, null=True)
    disallowed_reason = models.TextField(blank=True, null=True)

    raw_object = models.BinaryField(blank=True, null=True)
    raw_object.help_text = 'Pickled string version of the complete API returned content'

    # Exclude all deleted tweets - we keep them in so they aren't reimported
    # or added elsewhere
    objects = SocialPostManager()
    everything = AllSocialPostManager()

    def __unicode__(self):
        return u'{0} - {1} ({2})'.format(self.handle, self.account.type, self.messaged)

    class Meta:
	abstract = True
        # Content should be in ascending date order
        ordering = ('-high_priority', '-created_at', '-followers', 'handle')

    @property
    def entry_count(self):
        """
            Return how many times this handle has entered - we're only counting
            when they tweeted with an image - otherwise we'll exclude just tagged
            tweets - this isn't perfect - they might tweet something else and
            attach an image but should be ok
        """
        return get_model('social','socialpost').everything.filter(handle=self.handle).exclude(image_url=None).exclude(uid=self.uid).count()


    _rudness_level = models.IntegerField(blank=True, default=None) #Internal property. 0 if no forbidden words found or the level of the "rudder" word found or Null if the level has never been determined
    _rudness_level.verbose_name = "Rudness level"

    def check_rudness_level(self):
        """
        Define the highest level of the forbidden words of this post
        """
        self._rudness_level = 0
        forbidden_words = {fw['word']: fw['rudness_level'] for fw in get_model('social', 'forbiddenword').objects.filter(active=True).values('word', 'rudness_level')}
        for word in forbidden_words.keys():
            if word.lower() in self.content.lower():
                self._rudness_level = max(forbidden_words[word], self._rudness_level)

        try:
            if self._rudness_level >= settings.THRESHOLD_RUDNESS_LEVEL :
              self.entry_allowed = False
        except AttributeError:
          pass #if THRESHOLD_RUDNESS_LEVEL is not specified, do nothing

    @property
    def rudness_level(self):
        """
        Property method to access _rudness_level. 
        If the level has never been determined, it asks for its determination. It is then the responsability of the user to save that level with the rest of the model
        """
        must_save = False
        if(self._rudness_level == None):
            self.check_rudness_level()
            must_save = True

        return [self._rudness_level, must_save]
