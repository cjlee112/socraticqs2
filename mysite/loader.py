import ct.models
from django.utils import timezone
from django.contrib.auth.models import User
import sqlite3
import csv
import codecs
import os.path

def get_question_by_tem(c, title, errorModel):
    c.execute('select q.id, count(*) from questions q, error_models em, responses r where q.title=? and em.explanation=? and q.id=em.question_id and q.id=r.question_id group by q.id', (title, errorModel))
    return check_single(c.fetchall())

def get_question_by_title(c, title):
    l = []
    c.execute('select q.id, count(*) from questions q, responses r where q.title=? and q.id=r.question_id group by q.id', (title,))
    return check_single(c.fetchall())
    
def check_single(l):
    if len(l) == 1:
        return l[0]
    elif not l:
        return None
    raise KeyError('duplicated title: ' + title)

def load_error_models(errors, cq, author):
    errorModels = {}
    for eid,belief in errors:
        em = ct.models.ErrorModel.find_or_create(description=belief,
                                                 author=author)
        cem = cq.courseerrormodel_set.create(errorModel=em,
                                             course=cq.courselet.course,
                                             addedBy=author)
        errorModels[eid] = cem
    return errorModels

def import_error_models(c, qid, cq, author):
    c.execute('select id,belief from error_models where question_id=?', (qid,))
    return load_error_models(c.fetchall(), cq, author)

def import_responses(c, qid, cq, students):
    levels = [t[0] for t in ct.models.Response.CONF_CHOICES]
    c.execute('select uid,answer,confidence,submit_time,reasons from responses where question_id=?', (qid,))
    responses = {}
    for uid,answer,confidence,submit_time,reasons in c.fetchall():
        r = cq.response_set.create(atext=answer, atime=submit_time,
                                   confidence=levels[confidence],
                                   question=cq.question,
                                   selfeval=reasons, author=students[uid])
        responses[uid] = r
    return responses
                                  
def import_student_errors(c, qid, students, responses, errorModels):
    c.execute('select se.error_id,se.uid,se.submit_time from error_models em, student_errors se where em.question_id=? and em.id=se.error_id', (qid,))
    for error_id,uid,submit_time in c.fetchall():
        r = responses[uid]
        u = students[uid]
        cem = errorModels[error_id]
        r.studenterror_set.create(atime=submit_time, courseErrorModel=cem,
                                  author=u)

def import_students(c):
    students = {}
    c.execute('select * from students')
    for uid, fullname, username, date_added, added_by in c.fetchall():
        if not username:
            continue
        try:
            firstname, lastname = fullname.split()
            if firstname[-1] == ',':
                firstname, lastname = lastname, firstname[:-1]
        except ValueError:
            lastname = fullname
            firstname = ''
        try:
            u = User.objects.get(username=username)
        except User.DoesNotExist:
            u = User.objects.create_user(username, 'unknown', uid, 
                                     first_name=firstname, last_name=lastname)
            u.save()
        students[uid] = u
    return students
    

def import_courselet(c, csvfile, courselet, author, students, skipEmpty=True):
    questions = []
    with codecs.open(csvfile, 'r', encoding='utf-8') as ifile:
        for t in csv.reader(ifile):
            rustID, concepts, title, text, explanation = t[:5]
            if ct.models.Question.objects.filter(rustID=rustID).count() > 0:
                continue # already loaded in models database
            errors = t[5:]
            qid = None
            if len(errors) > 0:
                qid = get_question_by_tem(c, title, errors[0])
            if qid is None:
                qid = get_question_by_title(c, title)
            if skipEmpty and (qid is None or qid[1] == 0):
                continue
            q = ct.models.Question(title=title, qtext=text, answer=explanation,
                                   author=author, rustID=rustID)
            if concepts:
                for conceptID in concepts.split(','):
                    try:
                        q.concept = ct.models.Concept.\
                          get_from_sourceDB(conceptID, author)[0]
                    except KeyError:
                        print 'ignoring concept not found in wikipedia:', conceptID
                        continue
                    if courselet.concepts.filter(id=q.concept.id).count() == 0:
                        courselet.concepts.add(q.concept)
            q.save()
            cq = courselet.coursequestion_set.create(question=q, order=1,
                                                     addedBy=author)
            questions.append(cq)
            if qid: # import socraticqs data 
                qid = qid[0]
                responses = import_responses(c, qid, cq, students)
                errorModels = import_error_models(c, qid, cq, author)
                import_student_errors(c, qid, students, responses, errorModels)
            else: # just save our error models as-is
                load_error_models(enumerate(errors), cq, author)
    return questions

def import_courselets(course, csvdir, courseletTuples, dbfile, author=None):
    if author is None:
        author = course.addedBy
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    students = import_students(c)
    for courseletFile, title in courseletTuples:
        courseletFile = os.path.join(csvdir, courseletFile)
        courselet = course.courselet_set.create(title=title, addedBy=author)
        import_courselet(c, courseletFile, courselet, author, students, False)
    conn.close()

def import_course(csvfile, dbfile,
                  title='Introduction to Bioinformatics Theory', author=None):
    if author is None:
        author = User.objects.get(pk=1) # our default admin user
    course = ct.models.Course(title=title, addedBy=author)
    course.save()
    course.role_set.create(user=author, role=ct.models.Role.INSTRUCTOR)
    csvdir = os.path.dirname(csvfile)
    with codecs.open(csvfile, 'r', encoding='utf-8') as ifile:
        import_courselets(course, csvdir, csv.reader(ifile), dbfile, author)
    return course

if __name__ == '__main__':
    import_course('testdata/c260_2013/courselets.csv',
                  'testdata/c260_2013/course.db')
    
