import ct.models
from django.utils import timezone
from django.contrib.auth.models import User
import sqlite3
import csv
import codecs
import os.path
import random

class PhraseIndex(object):
    def __init__(self, t, nword=2):
        'construct phrase index for list of entries of the form [(id, text),]'
        self.nword = nword
        d = {}
        self.sizes = {}
        for i, text in t:
            n, l = self.get_phrases(text)
            self.sizes[i] = n # save numbers of phrases
            for j in range(n): # index all phrases in this text
                phrase = tuple(l[j:j + nword])
                try:
                    d[phrase].append(i)
                except KeyError:
                    d[phrase] = [i]
        self.d = d

    def get_phrases(self, text):
        'split into words, handling case < nword gracefully'
        l = text.split()
        if len(l) > self.nword:
            return len(l) - self.nword + 1, l
        else: # handle short phrases gracefully to allow matching
            return 1, l

    def __getitem__(self, text):
        'find entry with highest phrase match fraction'
        n, l = self.get_phrases(text)
        counts = {}
        for j in range(n):
            phrase = tuple(l[j:j + self.nword])
            for i in self.d.get(phrase, ()):
                counts[i] = counts.get(i, 0)  + 1
        l = []
        for i, c in counts.items(): # compute match fractions
            l.append((c / float(self.sizes[i]), i))
        l.sort()
        return l[-1][1] # return id with highest match fraction

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

def import_error_models2(c, qid, cq, author, emIndex):
    'find best phrase-match ErrorModels vs. socraticqs db for this qid'
    c.execute('select id,belief from error_models where question_id=?', (qid,))
    errorModels = {}
    for eid,belief in c.fetchall():
        em = ct.models.ErrorModel.objects.get(id=emIndex[belief])
        cem = cq.courseerrormodel_set.create(errorModel=em,
                                             course=cq.courselet.course,
                                             addedBy=author)
        errorModels[eid] = cem
    return errorModels

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
    

def import_students_anonymous(c, uidDict=None, email='unknown'):
    'import students using anonymization stored in uidDict'
    students = {}
    if not uidDict:
        uidDict = {}
    c.execute('select * from students')
    for uid, fullname, username, date_added, added_by in c.fetchall():
        if not uid:
            continue
        try:
            anonID = uidDict[uid]
        except KeyError:
            anonID = 'user%d' % hash(random.random())
            uidDict[uid] = anonID
        try:
            u = User.objects.get(username=anonID)
        except User.DoesNotExist:
            u = User.objects.create_user(anonID, email, None, 
                                     first_name='Student', last_name=anonID)
            u.save()
        students[uid] = u
    return students, uidDict

def import_students_anonymize_file(c, csvfile='anonymize.csv', **kwargs):
    'anonymize while importing, loading/updating uid -> anonID map in csvfile'
    uidDict = {}
    if os.path.exists(csvfile):
        with open(csvfile, 'rb') as ifile:
            for t in csv.reader(ifile):
                uidDict[t[0]] = t[1]
    students, uidDict = import_students_anonymous(c, uidDict, **kwargs)
    with open(csvfile, 'wb') as ifile:
        uidWriter = csv.writer(ifile)
        for t in uidDict.items():
            uidWriter.writerow(t)
    return students
    
def import_courselet2(c, csvfile, courselet, author, students, emIndex):
    questions = []
    with codecs.open(csvfile, 'r', encoding='utf-8') as ifile:
        for t in csv.reader(ifile):
            rustID, concepts, title, text, explanation = t[:5]
            q = ct.models.Question.objects.get(rustID=rustID)
            cq = courselet.coursequestion_set.create(question=q, order=1,
                                                     addedBy=author)
            questions.append(cq)
            qid = get_question_by_title(c, q.title)
            if qid: # import socraticqs data 
                qid = qid[0]
                responses = import_responses(c, qid, cq, students)
                errorModels = import_error_models2(c, qid, cq, author, emIndex)
                import_student_errors(c, qid, students, responses, errorModels)
    return questions

def import_course_question(c, courselet, q, qid, students, emIndex):
    '''import socraticqs data for specified qid to specified Question (rustID)
    by creating CourseQuestion etc. within this courselet'''
    n = courselet.courselesson_set.count() + \
                  courselet.coursequestion_set.count()
    cq = courselet.coursequestion_set.create(question=q, order=n,
                                             addedBy=courselet.addedBy)
    responses = import_responses(c, qid, cq, students)
    errorModels = import_error_models2(c, qid, cq, courselet.addedBy, emIndex)
    import_student_errors(c, qid, students, responses, errorModels)

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

def import_courselets(course, csvdir, courseletTuples, dbfile, emIndex,
                      author=None):
    if author is None:
        author = course.addedBy
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    students = import_students(c)
    for courseletFile, title in courseletTuples:
        courseletFile = os.path.join(csvdir, courseletFile)
        courselet = course.courselet_set.create(title=title, addedBy=author)
        import_courselet2(c, courseletFile, courselet, author, students,
                          emIndex)
    conn.close()

def import_course(csvfile, dbfile, emIndex=None,
                  title='Introduction to Bioinformatics Theory', author=None):
    if not author:
        author = User.objects.get(pk=1) # our default admin user
    if not emIndex: # build phrase index of all error models
        emIndex = index_error_models()
    course = ct.models.Course(title=title, addedBy=author)
    course.save()
    course.role_set.create(user=author, role=ct.models.Role.INSTRUCTOR)
    csvdir = os.path.dirname(csvfile)
    with codecs.open(csvfile, 'r', encoding='utf-8') as ifile:
        import_courselets(course, csvdir, csv.reader(ifile), dbfile, emIndex,
                          author)
    return course

def save_lesson(d, author, nodeID, rustID, title, text, sourceDB=None,
                sourceID=None):
    lesson = ct.models.Lesson(rustID=rustID, title=title, text=text,
                              addedBy=author)
    if sourceDB:
        lesson.sourceDB = sourceDB
        lesson.sourceID = sourceID
    lesson.save()
    d[nodeID] = lesson
    return lesson

def save_question(d, author, nodeID, rustID, title, qtext, answer, *errors):
    q = ct.models.Question(title=title, qtext=qtext, answer=answer,
                           author=author, rustID=rustID)
    q.save()
    d[nodeID] = q
    for error in errors:
        em = save_error_model(None, author, None, error)
        q.errorModels.add(em)
    return q

def save_error_model(d, author, nodeID, description, errorType=None,
                     alwaysAsk=False):
    em = ct.models.ErrorModel(description=description, author=author,
                              alwaysAsk=alwaysAsk)
    if errorType == 'abort':
        em.isAbort = True
    elif errorType == 'fail':
        em.isFail = True
    em.save()
    if nodeID is not None:
        d[nodeID] = em
    return em

def get_or_save_concept(concepts, conceptID, author, text='', debug=False):
    try: # get from local dict
        return concepts[conceptID]
    except KeyError:
        pass
    title = ' '.join(conceptID.split('_')) # space separated string
    try: # get from database
        concept = ct.models.Concept.objects.filter(title=title).all()[0]
    except IndexError:
        concept = None
    if not concept and debug: # quick test, skip wikipedia retrieval
        concept = ct.models.Concept(title=title, addedBy=author,
                                    description=text)
        concept.save()
    if not concept and not text:
        try: # get from wikipedia if possible
            concept = ct.models.Concept.get_from_sourceDB(title, author)[0]
        except KeyError:
            pass
    if not concept: # create it with whatever description we've got
        concept = ct.models.Concept(title=title, addedBy=author,
                                    description=text)
        concept.save()
        try: # link to wikipedia if matching page found
            lesson = ct.models.Lesson.get_from_sourceDB(title, author)
        except KeyError:
            pass
        else:
            concept.lessonlink_set.create(lesson=lesson, addedBy=author,
                    relationship=ct.models.LessonLink.IS)
    concepts[conceptID] = concept
    return concept

def save_concepts(links, d, author):
    concepts = {}
    for nodeID, relation, title in links: # save definitions
        if relation == 'defines':
            lesson = d[nodeID]
            concept = get_or_save_concept(concepts, title, author, lesson.text)
            concept.lessonlink_set.create(lesson=lesson, addedBy=author,
                        relationship=ct.models.LessonLink.DEFINES)
    return concepts

def save_concept_links(concepts, links, d, conceptErrors, author):
    rel = {
        'motivates':ct.models.LessonLink.MOTIVATES,
        'depends':ct.models.LessonLink.ASSUMES,
        'proves':ct.models.LessonLink.PROVES,
        'warning':ct.models.LessonLink.WARNS,
        'comment':ct.models.LessonLink.COMMENTS,
        'derivation':ct.models.LessonLink.DERIVES,
        'intro':ct.models.LessonLink.INTRODUCES,
        'informal-definition':ct.models.LessonLink.INFORMAL_DEFINITION,
        'formal-definition':ct.models.LessonLink.FORMAL_DEFINITION,
    }
    crel = dict(
        motivates=ct.models.ConceptLink.MOTIVATES,
        depends=ct.models.ConceptLink.DEPENDS,
    )
    rrel = {
        'informal-definition':ct.models.Resolution.INFORMAL_DEFINITION,
        'formal-definition':ct.models.Resolution.FORMAL_DEFINITION,
        'intro':ct.models.Resolution.INTRODUCES,
        'comment':ct.models.Resolution.COMMENTS,
        'warning':ct.models.Resolution.WARNS,
    }
    for em, conceptID in conceptErrors.values(): # link to concepts
        em.concept = get_or_save_concept(concepts, conceptID, author)
        em.save()
    for nodeID, relation, title in links:
        try: # is this an ErrorModel instead of a Concept?
            em, conceptID = conceptErrors[title]
        except KeyError:
            pass
        else:
            lesson = d[nodeID] # yes, so save resolution
            if isinstance(lesson, ct.models.Question):
                lesson.errorModels.add(em) # add em to this question
            else: # link lesson as Resolution of ErrorModel
                relationship = rrel.get(relation, ct.models.Resolution.EXPLAINS)
                r = ct.models.Resolution(lesson=lesson, errorModel=em,
                                        addedBy=author,
                                        relationship=relationship)
                r.save()
            continue # done processing this link
        if relation == 'defines':
            continue # already processed, nothing to do
        elif relation == 'tests': # link question to concept
            q = d[nodeID]
            q.concept = get_or_save_concept(concepts, title, author)
            q.save()
        else: # link lesson to concept
            lesson = d[nodeID]
            concept = get_or_save_concept(concepts, title, author)
            if isinstance(lesson, ct.models.Question):
                concept.lessonlink_set.create(question=lesson, addedBy=author,
                                            relationship=rel[relation])
            else:
                concept.lessonlink_set.create(lesson=lesson, addedBy=author,
                                            relationship=rel[relation])
            try: # does lesson define a concept?
                relationship = crel[relation]
                concept2 = ct.models.Concept.objects \
                  .filter(lessonlink__lesson=lesson,
                          lessonlink__relationship= \
                          ct.models.LessonLink.DEFINES).all()[0]
            except (KeyError,IndexError):
                pass
            else:  # if so, link its concept to concept
                cl = ct.models.ConceptLink(fromConcept=concept2,
                    toConcept=concept, addedBy=author,
                    relationship=relationship)
                cl.save()

def save_question_links(qlinks, d, author):
    'add links between lessons and questions'
    rel = dict(qintro=ct.models.QuestionLesson.CASE_ADDRESSED)
    for qID, relation, lessonID in qlinks:
        lesson = d[lessonID]
        q = d[qID]
        ql = ct.models.QuestionLesson(lesson=lesson, question=q,
                                      addedBy=author,
                                      relationship=rel[relation])
        ql.save()

def index_error_models():
    'construct phrase index of all error models in db'
    l = []
    for em in ct.models.ErrorModel.objects.all():
        l.append((em.id, em.description))
    return PhraseIndex(l)
        
def import_concept_lessons_csv(csvfile, author=None):
    d = {}
    links = []
    qlinks = []
    conceptErrors = {}
    if author is None:
        author = User.objects.get(pk=1) # our default admin user
    with codecs.open(csvfile, 'r', encoding='utf-8') as ifile:
        for row in csv.reader(ifile):
            if row[0] == 'lesson':
                save_lesson(d, author, *row[1:])
            elif row[0] == 'question':
                save_question(d, author, *row[1:])
            elif row[0] == 'error':
                nodeID, rustID, description, conceptID = row[1:]
                em = save_error_model(d, author, nodeID, description)
                conceptErrors[rustID] = (em, conceptID)
            elif row[0] == 'generic-error':
                save_error_model(d, author, None, row[1], row[2], True)
            elif row[0] == 'qlink':
                qlinks.append(row[1:])
            elif row[0] == 'conceptlink':
                links.append(row[1:])
            else: # parent-linked concept lesson
                conceptID = row[-1]
                lesson = save_lesson(d, author, *row[1:-1])
                links.append((row[1], row[0], conceptID))

    concepts = save_concepts(links, d, author)
    save_concept_links(concepts, links, d, conceptErrors, author)
    save_question_links(qlinks, d, author)


def import_selected_questions_csv(csvfile, rustIDs, author=None):
    'create Question objects for specified rustID(s) from csvfile'
    d = {}
    if author is None:
        author = User.objects.get(pk=1) # our default admin user
    with codecs.open(csvfile, 'r', encoding='utf-8') as ifile:
        for row in csv.reader(ifile):
            if row[0] == 'question' and row[2] in rustIDs:
                save_question(d, author, *row[1:])
    return d

def import_selected_questions(courselet, rustIDs, csvfile, dbfile,
                              emIndex=None, students=None):
    '''import specified questions (by rustID) from csvfile
    along with their associated socraticqs data, anonymized'''
    questions = import_selected_questions_csv(csvfile, rustIDs,
                                              courselet.addedBy)
    if not emIndex: # build phrase index of all error models
        emIndex = index_error_models()
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    if not students:
        students = import_students_anonymize_file(c)
    c.execute('select id, title from questions') # index socraticqs questions
    qIndex = PhraseIndex(c.fetchall())
    for q in questions.values():
        qid = qIndex[q.title] # find matching question in socraticqs db
        import_course_question(c, courselet, q, qid, students, emIndex)
    conn.close()
    
if __name__ == '__main__':
    import_concept_lessons_csv('testdata/c260_2013/concept_lessons.csv')
    import_course('testdata/c260_2013/courselets.csv',
                  'testdata/c260_2013/course.db')
    
