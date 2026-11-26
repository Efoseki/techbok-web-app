from django.test import TestCase
from .models import User
class CaseInsensitiveUsernameTests(TestCase):
    def test_username_is_normalized(self):
        user = User.objects.create_user(username="Demo.User", password="CaseSensitive123!")
        self.assertEqual(user.username, "demo.user")
        self.assertTrue(User.objects.get_by_natural_key("DEMO.USER").check_password("CaseSensitive123!"))
        self.assertFalse(user.check_password("casesensitive123!"))
