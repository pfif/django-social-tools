from django.test import TestCase
from socialtool.loading import get_model
from datetime import datetime

#A very ironic test case about java
class ForbiddenWordTagTestCase(TestCase):
    def setUp(self):
      #Creation of forbidden words
      ForbiddenWord = get_model('social', 'forbiddenword')
      self.swearwords = [
        ForbiddenWord(active=True, word='j2ee', rudness_level=5),
        ForbiddenWord(active=True, word='jsp', rudness_level=10),
        ForbiddenWord(active=True, word='job', rudness_level=2),
        ForbiddenWord(active=True, word='engineer', rudness_level=2),
        ForbiddenWord(active=False, word='jsf', rudness_level = 4)
      ]

      for fw in self.swearwords:
        fw.save()
      
      #Creation of a search term, dependancy of the social post
      self.searchterm = get_model('social', 'searchterm')(
        active = True,
        term = 'java'
      )
      self.searchterm.save()
      
      #Creation of the social post which rudness is to be found
      self.socialpost = get_model('social', 'socialpost')(
        created_at = datetime.now(),
        uid = 'javaisland',
        handle = 'javalover',
        search_term = self.searchterm,
        _rudness_level = 0
      )
      self.socialpost.save()

    def test_noswearword(self):
      """Test with no swearword. The level of a post without swear word is 0"""
      self.socialpost.content = "I love java !"
      self.socialpost.check_rudness_level()
      self.assertEqual(self.socialpost.rudness_level[0], 0)

    def test_oneswearword(self):
      """One little swearword is here to be found"""
      self.socialpost.content = "java developer job in London, 35k, contact via MP"
      self.socialpost.check_rudness_level()
      self.assertEqual(self.socialpost.rudness_level[0], 2)

    def test_severalswearword_samelevel(self):
      """Several swearword with the same level are to be found"""
      self.socialpost.content = "job alert ! java engineer position in Crosshat, 20k, contact @ITJobco"
      self.socialpost.check_rudness_level()
      self.assertEqual(self.socialpost.rudness_level[0], 2)

    def test_severalswearword_notsamelevel(self):
      """Several swearword are to be found. The level of rudness of the Social Post is the one of the rudder swearword"""
      self.socialpost.content = "Oh ! How I love j2ee ! and jsp has been design by geniuses"
      self.socialpost.check_rudness_level()
      self.assertEqual(self.socialpost.rudness_level[0], 10)

    def test_severalswearword_newlevel(self):
      """If a swearword is activated at one point and that the rudness is computed again, it must change"""
      self.socialpost._rudness_level = 5
      self.socialpost.content = "Oh ! How I love j2ee ! and jsp has been design by geniuses"
      self.socialpost.check_rudness_level()
      self.assertEqual(self.socialpost.rudness_level[0], 10)

    def test_inactiveswearwords(self):
      """Inactive word must not be taken in account"""
      self.socialpost.content = "jsf <3"
      self.socialpost.check_rudness_level()
      self.assertEqual(self.socialpost.rudness_level[0], 0)

    def test_inactiveswearwords_activeswearwords(self):
      """Only active swearwords must be found"""
      self.socialpost.content = "jsp > jsf"
      self.socialpost.check_rudness_level()
      self.assertEqual(self.socialpost.rudness_level[0], 10)

    def test_getterneversendsnone(self):
      """When requested but not computed yet, the rudness of a Social Post must be computed."""
      self.socialpost._rudness_level = None
      self.socialpost.content = "java developper job in London, 35k, contact via MP"
      self.assertEqual(self.socialpost.rudness_level, [2, True])
 
    def test_getterneversendnone_noswearword(self):
      """When requested but not computed yet, the rudness of a Social Post must be computed."""
      self.socialpost._rudness_level = None
      self.socialpost.content = "I love java !"
      self.assertEqual(self.socialpost.rudness_level, [0, True])

    def test_oneswearword_uppercase(self):
      """A word must be found even if its case is WeIrD"""
      self.socialpost.content = "JsP new version out"
      self.socialpost.check_rudness_level()
      self.assertEqual(self.socialpost.rudness_level[0], 10)
