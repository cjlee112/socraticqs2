import pytest
from accounts.models import Profile, Instructor
from ctms.models import Invite

@pytest.mark.django_db
def test_send_logged(user, pending_invite):
    pending_invite.send_mail(user)
    profile = Profile.objects.get(user=user)
    assert profile.data['invitations_sent'][pending_invite.code]['email'] == pending_invite.email


@pytest.mark.django_db
def test_mailto_invite(user, enroll_unit_code, dkim_validation_dict):
    instructor = Instructor.objects.create(user=user, institution='institute', what_do_you_teach='something')
    invite = Invite.get_or_create_mailto(user, enroll_unit_code.enrollCode)
    assert invite.type == 'mailto' and invite.status == 'pending'
    assert invite.get_mailto_url().startswith('mailto:')
    assert user.profile.is_provisional()
    invite.mailto_acceptance('mutated@example.com', dkim_validation_dict['dkimValidation'], user.username)
    profile = Profile.objects.get(user=user)
    assert not profile.is_provisional()
    assert profile.user.email == 'mutated@example.com'



@pytest.mark.django_db
def test_create_for_user(user, enroll_unit_code):
    instructor = Instructor.objects.create(user=user, institution='institute', what_do_you_teach='something')
    invite = Invite.create_for_user(user, enroll_unit_code.enrollCode, data=dict(page='/boo'))
    profile = Profile.objects.get(user=user)
    assert profile.data['invitations_sent'][invite.code]['email'] == invite.email

