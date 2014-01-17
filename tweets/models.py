from django.db import models
from django.contrib.auth.models import User
from managers import TweetManager, AllTweetManager


class MarketAccount(models.Model):
    handle = models.CharField(max_length=100)
    consumer_secret = models.CharField(max_length=100)
    consumer_key = models.CharField(max_length=100)
    access_token_secret = models.CharField(max_length=100)
    access_token_key = models.CharField(max_length=100)

    def __unicode__(self):
        return u'{0} ({1})'.format(self.handle, self.pk)


class Message(models.Model):
    MESSAGE_TYPES = (
        ('f', 'Fail'),
        ('s', 'Success'),
    )

    copy = models.CharField(max_length=140)
    account = models.ForeignKey(MarketAccount)
    type = models.CharField(max_length=1, choices=MESSAGE_TYPES)

    def __unicode__(self):
        return u'{0} ({1}...)'.format(self.account, self.copy[:30])


class BannedUser(models.Model):
    handle = models.CharField(max_length=100, unique=True)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.handle


class Tweet(models.Model):
    created_at = models.DateTimeField()
    created_at.verbose_name = 'tweet date'
    uid = models.CharField(max_length=100, unique=True)
    handle = models.CharField(max_length=100)
    followers = models.IntegerField(blank=True, null=True)
    content = models.CharField(max_length=150)
    content.verbose_name = 'user\'s tweet'
    image_url = models.URLField(max_length=255, blank=True, null=True)
    tweeted = models.BooleanField(default=False)
    tweeted.verbose_name = 'tweet status'
    approved = models.BooleanField(default=False)
    high_priority = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    entry_allowed = models.BooleanField(default=True)
    photoshop = models.ImageField(upload_to='uploads', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    notes.verbose_name = 'internal notes'
    account = models.ForeignKey(MarketAccount, blank=True, null=True)
    account.verbose_name = 'adidas\' handle'
    sent_tweet = models.CharField(max_length=140, blank=True, null=True)
    artworker = models.ForeignKey(User, related_name='artworker', blank=True, null=True)
    tweeted_by = models.ForeignKey(User, related_name='tweeter', blank=True, null=True)
    tweeted_at = models.DateTimeField(blank=True, null=True)
    tweet_id = models.CharField(max_length=100, blank=True, null=True)
    disallowed_reason = models.TextField(blank=True, null=True)

    # TODO: Rework into a foreign key model that stores an adjustment with a type
    # for labelling rather than directly on the model
    auto_base = models.ImageField(upload_to='uploads', blank=True, null=True)
    auto_photoshop_1 = models.ImageField(upload_to='uploads', blank=True, null=True)
    auto_photoshop_2 = models.ImageField(upload_to='uploads', blank=True, null=True)
    auto_photoshop_3 = models.ImageField(upload_to='uploads', blank=True, null=True)
    auto_compose_1 = models.ImageField(upload_to='uploads', blank=True, null=True)
    auto_compose_2 = models.ImageField(upload_to='uploads', blank=True, null=True)
    auto_compose_3 = models.ImageField(upload_to='uploads', blank=True, null=True)

    def __unicode__(self):
        return u'{0} - {1} ({2})'.format(self.handle, self.account, self.tweeted)

    class Meta:
        # Tweets should be in ascending date order
        ordering = ('-high_priority', '-created_at', '-followers', 'handle')

    @property
    def has_existing_graphic(self):
        """
            Check if this tweet already has an attached graphic - we may deny
            entry if they have already entered and had a response
        """
        return Tweet.everything.filter(handle=self.handle).exclude(photoshop='').exclude(uid=self.uid).count() > 0

    @property
    def entry_count(self):
        """
            Return how many times this handle has entered - we're only counting
            when they tweeted with an image - otherwise we'll exclude just tagged
            tweets - this isn't perfect - they might tweet something else and
            attach an image but should be ok
        """
        return Tweet.everything.filter(handle=self.handle).exclude(image_url=None).exclude(uid=self.uid).count()

    # Exclude all deleted tweets - we keep them in so they aren't reimported
    # or added elsewhere
    objects = TweetManager()
    everything = AllTweetManager()


class SearchTerm(models.Model):
    active = models.BooleanField(default=False)
    term = models.CharField(max_length=100)

    def __unicode__(self):
        return u'{0} ({1})'.format(self.term, self.active)
