"""
Identity of the Egyptian fork (Mayan EDMS trademark policy 1.1, section 5):
the fork does not present itself as Mayan EDMS nor show its logo, credits
it as the upstream project and keeps its copyright notice.
"""
from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import TestCase

import mayan

from ..links import link_support


class EgyptianIdentityTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            email="identity@example.com", password="identity-password",
            username="identity_test"
        )
        # English pages, whatever the default language of the installation.
        self.user.locale_profile.language = "en"
        self.user.locale_profile.save()

    def test_metadata(self):
        self.assertEqual(mayan.__title__, "Egyptian")
        self.assertEqual(mayan.__upstream_title__, "Mayan EDMS")
        self.assertEqual(mayan.__copyright__, "Copyright 2026 Roberto Rosario")
        self.assertEqual(link_support.url, "https://egyptian-apps.mypalace.ca/forum/")
        self.assertFalse(apps.is_installed("mayan.apps.fundraisers"))

    def test_login_page(self):
        response = self.client.get("/authentication/login/")
        self.assertContains(response, "appearance/images/egyptian-login.png")
        self.assertContains(response, "appearance/images/egyptian-favicon.ico")
        self.assertContains(response, "content=\"Egyptian\" name=\"application-name\"")
        self.assertContains(response, "Copyright 2026 Roberto Rosario")
        self.assertNotContains(response, "login-top.jpg")
        self.assertNotContains(response, "Guided Demo")

    def test_favicon(self):
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("appearance/images/egyptian-favicon.ico"))

    def test_pages(self):
        self.client.force_login(user=self.user)
        # Top bar and main menu: application root, the pages are loaded in it.
        response = self.client.get("/")
        self.assertContains(response, "class=\"egyptian-logo\"")
        self.assertContains(response, "Based on Mayan EDMS®")
        self.assertNotContains(response, "icon-mayan-edms-logo")

        response = self.client.get("/about/")
        self.assertContains(response, "egyptian-about.png")
        self.assertContains(response, "is a modified version (fork) of Mayan EDMS")
        self.assertContains(response, "Copyright 2026 Roberto Rosario")
        self.assertContains(response, "Copyright 2026 mypalace.ca")
        self.assertNotContains(response, "about-top.jpg")

        response = self.client.get("/license/")
        self.assertContains(response, "Egyptian is a modified version of Mayan EDMS")
        self.assertContains(response, "GNU General Public License")

        response = self.client.get("/trademark_policy/")
        self.assertContains(response, "Trademarks")
        self.assertContains(response, "Egyptian is a fork based on Mayan EDMS")
        self.assertContains(response, "Mayan EDMS Trademark Policy")
