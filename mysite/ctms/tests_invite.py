import pytest
from accounts.models import Profile

@pytest.mark.django_db
def test_send_logged(user, pending_invite):
    pending_invite.send_mail(user)
    profile = Profile.objects.get(user=user)
    assert profile.data['invitations_sent'][pending_invite.code]['email'] == pending_invite.email


