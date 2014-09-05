import django
django.setup()
import ct.models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import csv
import codecs

teacher = User.objects.get(pk=1) # our default admin user

course = ct.models.Course(title='Introduction to Bioinformatics Theory',
                          addedBy=teacher)
course.save()

u = course.courselet_set.create(title='Conditional Probability', addedBy=teacher)

course.role_set.create(user=teacher, role=ct.models.Role.INSTRUCTOR)

q = ct.models.Question(title='A Great Question',
                       qtext='If Peter Piper picked a peck of peppers...',
                       answer='The answer is: there is no spoon.',
                       author=teacher)
q.save()

cq = u.coursequestion_set.create(question=q, order=1, addedBy=teacher)
cq.save()

em = ct.models.ErrorModel(description='You made a boo-boo!', author=teacher)
em.save()
cem = cq.courseerrormodel_set.create(errorModel=em, course=course,
                                     addedBy=teacher)

try:
    john = User.objects.get(pk=2) # our first student
except ObjectDoesNotExist:        
    john = User.objects.create_user('john', 'lennon@thebeatles.com',
                                    'johnpassword')
    john.save()

r = q.response_set.create(atext='I really have no idea.', author=john)

se = r.studenterror_set.create(courseErrorModel=cem, author=john)

em2 = ct.models.ErrorModel(description='very common, very silly error',
                           alwaysAsk=True, author=teacher)
em2.save()

q2 = ct.models.Question(title='Another Question',
                       qtext='If Bob has 7 apples...',
                       answer='If life gives you apples, make applesauce.',
                       author=john)
q2.save()

def load_csv(csvfile, courselet, author):
    with codecs.open(csvfile, 'r', encoding='utf-8') as ifile:
        reader = csv.reader(ifile)
        for row in reader:
            q = ct.models.Question(title=row[0], qtext=row[1], answer=row[2],
                                   author=author)
            q.save()
            cq = courselet.coursequestion_set.create(question=q, order=1,
                                                     addedBy=author)
            for e in row[3:]:
                em = ct.models.ErrorModel(description=e, author=author)
                em.save()
                cem = cq.courseerrormodel_set.create(errorModel=em,
                                                     course=courselet.course,
                                                     addedBy=author)
                

load_csv('ct/lec2.csv', u, teacher) # try loading some real data

ny, nyLesson = ct.models.Concept.get_from_sourceDB('New York', teacher)
