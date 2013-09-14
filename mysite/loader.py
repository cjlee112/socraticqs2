import ct.models
from django.utils import timezone
from django.contrib.auth.models import User
import sqlite3
import csv

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

def import_error_models(c, qid, q):
    c.execute('select id,belief from error_models where question_id=?', (qid,))
    errorModels = {}
    for eid,belief in c.fetchall():
        em = q.errormodel_set.create(description=belief, isAbort=False)
        errorModels[eid] = em
    return errorModels

def import_responses(c, qid, q, students, levels=('guess', 'unsure', 'sure')):
    c.execute('select uid,answer,confidence,submit_time,reasons from responses where question_id=?', (qid,))
    responses = {}
    for uid,answer,confidence,submit_time,reasons in c.fetchall():
        r = q.response_set.create(atext=answer, atime=submit_time,
                                  confidence=levels[confidence], 
                                  selfeval=reasons, author=students[uid])
        responses[uid] = r
    return responses
                                  
def import_student_errors(c, qid, students, responses, errorModels):
    c.execute('select se.error_id,se.uid,se.submit_time from error_models em, student_errors se where em.question_id=? and em.id=se.error_id', (qid,))
    for error_id,uid,submit_time in c.fetchall():
        r = responses[uid]
        u = students[uid]
        em = errorModels[error_id]
        r.studenterror_set.create(atime=submit_time, errorModel=em, author=u)

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
        u = User.objects.create_user(username, 'unknown', uid, 
                                     first_name=firstname, last_name=lastname)
        u.save()
        students[uid] = u
    return students
    

def import_socraticqs(dbfile, csvfile, skipEmpty=True):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    students = import_students(c)
    questions = []
    with open(csvfile, 'Ub') as ifile:
        for t in csv.reader(ifile):
            title, text, explanation, nerror = t[1:5]
            if int(nerror) > 0:
                qid = get_question_by_tem(c, title, t[5])
            else:
                qid = get_question_by_title(c, title)
            if qid is None or (skipEmpty and qid[1] == 0):
                continue
            else:
                qid = qid[0]
            q = ct.models.Question(title=title, qtext=text, answer=explanation)
            q.save()
            questions.append(q)
            responses = import_responses(c, qid, q, students)
            errorModels = import_error_models(c, qid, q)
            import_student_errors(c, qid, students, responses, errorModels)
    return questions



