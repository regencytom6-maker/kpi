import unittest
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

class OperatorDashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.operator = User.objects.create_user(username='operator1', password='testpass', role='operator')
        self.client.login(username='operator1', password='testpass')
        # Optionally, create some operator history, stats, and assignments here if your models allow

    def test_dashboard_renders(self):
        url = reverse('dashboards:workflow_chart')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Operator Dashboard')
        self.assertContains(response, 'Download History')
        self.assertContains(response, 'My History')
        self.assertContains(response, 'My Statistics')
        self.assertContains(response, 'Current Assignments')

    def test_history_table_present(self):
        url = reverse('dashboards:workflow_chart')
        response = self.client.get(url)
        self.assertIn(b'id=\"operator-history\"', response.content)

    def test_download_button_present(self):
        url = reverse('dashboards:workflow_chart')
        response = self.client.get(url)
        self.assertIn(b'Download History', response.content)

    def test_workflow_cards_clickable(self):
        url = reverse('dashboards:workflow_chart')
        response = self.client.get(url)
        self.assertIn(b'goToBatchDetail', response.content)

if __name__ == '__main__':
    unittest.main()
