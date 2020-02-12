"""
Chat page.
"""
import json

from django.urls import reverse


class Session:
    """
    Implements Session interface aka PageObject pattern.

    Availale method:
    :send_text:
    :send_option:
    :continue:
    :view_updates:
    :next_thread:
    :send_diffent:
    :send_same:
    """
    def __init__(self, enroll_unit_code, client, *args, **kwargs):
        self.json_content = None
        self.chat_id = None
        self.history = None
        self.enroll_unit_code = enroll_unit_code
        self.client = client

    def create_session(self):
        response = self.client.get(
            reverse(
                'chat:init_chat_api',
                kwargs={
                    'enroll_key': self.enroll_unit_code.enrollCode,
                    'chat_id': 0
                }
            ),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        json_content = json.loads(response.content)
        self.chat_id = json_content['id']
        response = self.client.get(
            reverse('chat:chat_enroll', args=(self.enroll_unit_code.enrollCode, self.chat_id)), follow=True
        )
        response = self.client.get(reverse('chat:history'), {'chat_id': self.chat_id}, follow=True)
        self.json_content = json.loads(response.content)
        self.history = self.json_content.get('addMessages')

    def show_input(self):
        return self.json_content.get('input', {}).get('options') if self.json_content else None

    def show_messages(self):
        return self.history

    def show_extras(self):
        return self.json_content.get('extras')

    def send_text(self):
        pass
