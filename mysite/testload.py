import ct.models
from django.utils import timezone
from django.contrib.auth.models import User

q = ct.models.Question(title='A Great Question',
                       qtext='If Peter Piper picked a peck of peppers...',
                       answer='The answer is: there is no spoon.')
q.save()

em = q.errormodel_set.create(description='You made a boo-boo!', isAbort=False)

john = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
john.save()

r = q.response_set.create(atext='I really have no idea.', 
                          atime=timezone.now(),
                          author=john)

se = r.studenterror_set.create(atime=timezone.now(),
                               errorModel=em,
                               author=john)
