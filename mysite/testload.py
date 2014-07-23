import ct.models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


course = ct.models.Course(title='Introduction to Bioinformatics Theory')
course.save()

u = course.unit_set.create(title='Conditional Probability')

teacher = User.objects.get(pk=1) # our default admin user
course.role_set.create(user=teacher, role=ct.models.Role.INSTRUCTOR)

q = ct.models.Question(title='A Great Question',
                       qtext='If Peter Piper picked a peck of peppers...',
                       answer='The answer is: there is no spoon.',
                       author=teacher)
q.save()

ut = u.unitq_set.create(question=q, order=1)

em = q.errormodel_set.create(description='You made a boo-boo!')

try:
    john = User.objects.get(pk=2) # our first student
except ObjectDoesNotExist:        
    john = User.objects.create_user('john', 'lennon@thebeatles.com',
                                    'johnpassword')
    john.save()

r = q.response_set.create(atext='I really have no idea.', 
                          atime=timezone.now(),
                          author=john)

se = r.studenterror_set.create(atime=timezone.now(),
                               errorModel=em,
                               author=john)
