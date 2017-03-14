#!/usr/bin/env python
import optparse
import os
import platform
import sys
import codecs
import sqlite3
import csv
import pandas as pd

conn = sqlite3.connect(':memory:')
c = conn.cursor()
c.execute('create table if not exists questions (exam int, id int, question_num int, correct int, UNIQUE(exam, id, question_num) ON CONFLICT REPLACE);')
c.execute('create table if not exists assessment (question_num int, exam1 int, exam2 int, distractors int, UNIQUE(question_num) ON CONFLICT REPLACE);')
c.execute('create table if not exists student_list (id int, UNIQUE(id) ON CONFLICT REPLACE);')
conn.commit()
c.close()

def isFloat(s):
    try:
        return float(s)
    except:
        return None

def isInt(num):
    try:
        return int(round(float(num)))
    except:
        return None



def isReturnFile(myfile):
    if os.path.abspath(os.path.expanduser(myfile.strip())) != False:
        return os.path.abspath(os.path.expanduser(myfile.strip()))
    else:
        print 'You can\'t save to that location'
        sys.exit()

def LoadQuestions(filename, exam, conn):
    reader = csv.reader(open(os.path.abspath(os.path.expanduser(filename)), 'rU'))
    c = conn.cursor()
    Key = None
    exam = isInt(exam)
    for row in reader:
        if Key == None:
            i = 3
            end = isInt(row[2]) + 3
            Key = []
            while (i < end):
                Key.append(row[i])
                i = i + 1
        else:
            studentid = isInt(row[1])
            i = 3
            qnum = 1
            keyi = 0
            while (i < end):
                if 0 <= i < len(row):
                    if Key[keyi] == row[i]:
                        correct = 1
                    else:
                        correct = 0
                else:
                    correct = 0
                if exam != None and qnum != None and studentid != None:
                    mylist = (exam, studentid, qnum, correct)
                    c.execute('INSERT INTO questions (exam, id, question_num, correct) VALUES(?,?,?,?)',mylist)
                    conn.commit()
                keyi = keyi + 1
                i = i + 1
                qnum = qnum + 1
    c.close()

def LoadAssessment(filename,conn,igroup=None):
    reader = csv.DictReader(open(os.path.abspath(os.path.expanduser(filename)), 'rU'))
    c = conn.cursor()
    for row in reader:
        exam1 = None
        exam2 = None
        q = None
        qgroup = None
        distractors = None
        for name in row.keys():
            if name.lower().strip() == 'exam1' or name.lower().strip() == 'pretest':
                exam1 = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
            elif name.lower().strip() == 'exam2' or name.lower().strip() == 'posttest':
                exam2 = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
            elif name.lower().strip() == 'q' or name.lower().strip() == 'question':
                q = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
            elif name.lower().strip() == 'group' or name.lower().strip() == 'groups':
                qgroup = unicode(str(row.get(name,'')).strip().lower(), "utf8")
            elif name.lower().strip() == 'options' or name.lower().strip() == 'answers' or name.lower().strip() == 'distractors':
                distractors = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
        if exam1 != None and exam2 != None and q != None:
            mylist = (exam1, exam2, q, distractors)
            if igroup != None:
                qgroup = qgroup.replace(' ',',')
                qgroupList = qgroup.split(',')
                nqgroupList = [ isInt(x) for x in qgroupList ]
                if igroup in nqgroupList:
                    c.execute('INSERT INTO assessment(exam1, exam2, question_num, distractors) VALUES(?,?,?,?)',mylist)
            else:
                c.execute('INSERT INTO assessment(exam1, exam2, question_num, distractors) VALUES(?,?,?,?)',mylist)
            conn.commit()
    c.close()

def LoadStudents(filename,conn):
    reader = csv.DictReader(open(os.path.abspath(os.path.expanduser(filename)), 'rU'))
    c = conn.cursor()
    for row in reader:
        id = None
        for name in row.keys():
            if name.lower().strip() == 'id' or name.lower().strip() == 'studentid':
                id = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
        if id != None:
            mylist = (id,)
            c.execute('INSERT INTO student_list(id) VALUES(?)',mylist)
            conn.commit()
    c.close()


def GenerateSelect(conn):
    c = conn.cursor()
    c.execute("SELECT firstResult.question_num AS q, firstResult.s AS Exam1, finalResult.s AS Exam2, firstResult.distractors AS d FROM (SELECT assessment.question_num, assessment.distractors, AVG(correct) As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1 GROUP BY questions.question_num) AS firstResult JOIN (SELECT assessment.question_num, AVG(correct) AS s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2 GROUP BY questions.question_num) AS finalResult ON firstResult.question_num=finalResult.question_num")
    results = c.fetchall()
    dataset = []
    for row in results:
        dataset.append(row)
    c.close()
    return pd.DataFrame(dataset,columns=('Q','Exam1','Exam2','Options'))

def GenerateStudentSelect(conn):
    c = conn.cursor()
    c.execute("SELECT firstResult.id, firstResult.s AS Exam1, finalResult.s AS Exam2 FROM (SELECT questions.id AS id, AVG(correct) As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1 GROUP BY questions.id) AS firstResult JOIN (SELECT questions.id AS id, AVG(correct) As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2 GROUP BY questions.id) AS finalResult ON firstResult.id=finalResult.id ORDER BY finalResult.s DESC")
    results = c.fetchall()
    dataset = []
    for row in results:
        dataset.append(row)
    c.close()
    return pd.DataFrame(dataset,columns=('id','Exam1','Exam2'))

def GeneratePL(conn, studentgroup=None):
    c = conn.cursor()
    if studentgroup==True:
        select = 'mytable.id AS id'
        groupby = 'mytable.id'
        cmTitle = 'id'
    else:
        select = 'mytable.q AS Q'
        groupby = 'mytable.q'
        cmTitle = 'Q'
    c.execute('SELECT ' + select + ', AVG(mytable.PL) AS PL FROM (SELECT pretest.id AS id, pretest.qn AS q, CASE WHEN pretest.s=0 THEN posttest.s ELSE 0 END AS PL FROM (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1) AS pretest JOIN (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2) AS posttest ON pretest.id=posttest.id AND pretest.qn=posttest.qn) AS mytable GROUP BY ' + groupby + ' ORDER BY ' + groupby)
    results = c.fetchall()
    dataset = []
    for row in results:
        dataset.append(row)
    c.close()
    return pd.DataFrame(dataset,columns=(cmTitle,'PL'))

def GenerateRL(conn, studentgroup=None):
    c = conn.cursor()
    if studentgroup==True:
        select = 'mytable.id AS id'
        groupby = 'mytable.id'
        cmTitle = 'id'
    else:
        select = 'mytable.q AS Q'
        groupby = 'mytable.q'
        cmTitle = 'Q'
    c.execute('SELECT ' + select + ', AVG(mytable.RL) AS RL FROM (SELECT pretest.id AS id, pretest.qn AS q, CASE WHEN pretest.s=1 THEN posttest.s ELSE 0 END AS RL FROM (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1) AS pretest JOIN (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2) AS posttest ON pretest.id=posttest.id AND pretest.qn=posttest.qn) AS mytable GROUP BY ' + groupby + ' ORDER BY ' + groupby)
    results = c.fetchall()
    dataset = []
    for row in results:
        dataset.append(row)
    c.close()
    return pd.DataFrame(dataset,columns=(cmTitle,'RL'))

def GenerateZL(conn, studentgroup=None):
    c = conn.cursor()
    if studentgroup==True:
        select = 'mytable.id AS id'
        groupby = 'mytable.id'
        cmTitle = 'id'
    else:
        select = 'mytable.q AS Q'
        groupby = 'mytable.q'
        cmTitle = 'Q'
    c.execute('SELECT ' + select + ', AVG(mytable.ZL) AS ZL FROM (SELECT pretest.id AS id, pretest.qn AS q, CASE WHEN (pretest.s=0 AND posttest.s=0) THEN 1 ELSE 0 END AS ZL FROM (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1) AS pretest JOIN (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2) AS posttest ON pretest.id=posttest.id AND pretest.qn=posttest.qn) AS mytable GROUP BY ' + groupby + ' ORDER BY ' + groupby)
    results = c.fetchall()
    dataset = []
    for row in results:
        dataset.append(row)
    c.close()
    return pd.DataFrame(dataset,columns=(cmTitle,'ZL'))

def GenerateNL(conn, studentgroup=None):
    c = conn.cursor()
    if studentgroup==True:
        select = 'mytable.id AS id'
        groupby = 'mytable.id'
        cmTitle = 'id'
    else:
        select = 'mytable.q AS Q'
        groupby = 'mytable.q'
        cmTitle = 'Q'
    c.execute('SELECT ' + select + ', AVG(mytable.NL) AS NL FROM (SELECT pretest.id AS id, pretest.qn AS q, CASE WHEN pretest.s=1 AND posttest.s=0 THEN 1 ELSE 0 END AS NL FROM (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1) AS pretest JOIN (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2) AS posttest ON pretest.id=posttest.id AND pretest.qn=posttest.qn) AS mytable GROUP BY ' + groupby + ' ORDER BY ' + groupby)
    results = c.fetchall()
    dataset = []
    for row in results:
        dataset.append(row)
    c.close()
    return pd.DataFrame(dataset,columns=(cmTitle,'NL'))

def Gamma(x):
    pl = x['PL']
    zl = x['ZL']
    rl = x['RL']
    nl = x['NL']
    numoptions = x['Options']
    if isInt(numoptions)>0:
        egamma = (numoptions*(nl+pl*numoptions+rl-1))/((numoptions-1)**2)
        return egamma
    else:
        return None

def Mu(x):
    pl = x['PL']
    zl = x['ZL']
    rl = x['RL']
    nl = x['NL']
    numoptions = x['Options']
    if isInt(numoptions)>0:
        emu = ((nl+rl)-1)/(numoptions-1)+nl+rl
        return emu
    else:
        return None

def Alpha(x):
    pl = x['PL']
    zl = x['ZL']
    rl = x['RL']
    nl = x['NL']
    numoptions = x['Options']
    if isInt(numoptions)>0:
        ealpha = (numoptions*(nl*numoptions+pl+rl-1))/((numoptions-1)**2)
        return ealpha
    else:
        return None

def Flow(x):
    pl = x['PL']
    zl = x['ZL']
    rl = x['RL']
    nl = x['NL']
    numoptions = x['Options']
    if isInt(numoptions)>0:
        eflow = (numoptions*(pl-nl))/(numoptions-1)
        return eflow
    else:
        return None


def main():
    global conn
    desc = 'Calculate assessment data from Scantron format'
    p = optparse.OptionParser(description=desc)
    p.add_option('--pretest','-p', dest="pretest", help="Set pre-test file", default='exam1.csv', metavar='"<File Path>"')
    p.add_option('--posttest','-f', dest="posttest", help="Set post-test file", default='exam2.csv', metavar='"<File Path>"')
    p.add_option('--students','-s', dest="students", help="Set student ids file", default='students.csv', metavar='"<File Path>"')
    p.add_option('--assessment','-a', dest="assessment", help="Set assessment questions file", default='assessment_questions.csv', metavar='"<File Path>"')
    p.add_option('--group', help="Specify a subset of the assessment questions using a group", type="int", dest="group")

    (options, arguments) = p.parse_args()

    run = True
    if len(options.pretest.strip()) > 0:
        if os.path.isfile(os.path.abspath(os.path.expanduser(options.pretest.strip()))) != False:
            LoadQuestions(os.path.abspath(os.path.expanduser(options.pretest.strip())),1,conn)
        else:
            run = False
            print "You must specify a pretest file."
    else:
        run = False
        print "You must specify a pretest file."

    if len(options.posttest.strip()) > 0:
        if os.path.isfile(os.path.abspath(os.path.expanduser(options.posttest.strip()))) != False:
            LoadQuestions(os.path.abspath(os.path.expanduser(options.posttest.strip())),2,conn)
        else:
            run = False
            print "You must specify a posttest file."
    else:
        run = False
        print "You must specify a posttest file."

    if len(options.students.strip()) > 0:
        if os.path.isfile(os.path.abspath(os.path.expanduser(options.students.strip()))) != False:
            LoadStudents(os.path.abspath(os.path.expanduser(options.students.strip())),conn)
        else:
            run = False
            print "You must specify a file containing a list of student IDs."
    else:
        run = False
        print "You must specify a file containing a list of student IDs."

    if len(options.assessment.strip()) > 0:
        if os.path.isfile(os.path.abspath(os.path.expanduser(options.assessment.strip()))) != False:
            if options.group != None and options.group != False and len(str(options.group))>0:
                LoadAssessment(os.path.abspath(os.path.expanduser(options.assessment.strip())),conn, options.group)
            else:
                LoadAssessment(os.path.abspath(os.path.expanduser(options.assessment.strip())),conn)
        else:
            run = False
            print "You must specify an assessment mapping file."
    else:
        run = False
        print "You must specify an assessment mapping file."

    if run == True:
        questions = GenerateSelect(conn)
        studentsSel = GenerateStudentSelect(conn)
        qoptions = questions[['Options']]
        pl = GeneratePL(conn)
        rl = GenerateRL(conn)
        zl = GenerateZL(conn)
        nl = GenerateNL(conn)
        pt = rl['RL'] + nl['NL']
        pot = rl['RL'] + pl['PL']
        delta = pot - pt
        pt = pd.DataFrame(pt,columns=('PreTest',))
        pot = pd.DataFrame(pot,columns=('PostTest',))
        delta = pd.DataFrame(delta,columns=('Delta',))
        overall = pd.concat([pl,rl[['RL']],zl[['ZL']],nl[['NL']],pt,pot,delta,qoptions],axis=1)
        overall['Gamma'] = overall.apply(Gamma, axis=1)
        overall['Mu'] = overall.apply(Mu, axis=1)
        overall['Alpha'] = overall.apply(Alpha, axis=1)
        overall['Flow'] = overall.apply(Flow, axis=1)
        del questions['Options']
        del overall['Options']
        overall.to_csv('Walstad_Wagner_types.csv', index=False)

        questions.to_csv('Questions_output.csv', index=False)
        studentsSel.to_csv('Student_output.csv', index=False)
        pl = GeneratePL(conn,True)
        rl = GenerateRL(conn,True)
        zl = GenerateZL(conn,True)
        nl = GenerateNL(conn,True)
        pt = rl['RL'] + nl['NL']
        pot = rl['RL'] + pl['PL']
        delta = pot - pt
        pt = pd.DataFrame(pt,columns=('PreTest',))
        pot = pd.DataFrame(pot,columns=('PostTest',))
        delta = pd.DataFrame(delta,columns=('Delta',))
        overall = pd.concat([pl,rl[['RL']],zl[['ZL']],nl[['NL']],pt,pot,delta],axis=1)
        overall.to_csv('Walstad_Wagner_types_by_student.csv', index=False)

if __name__ == '__main__':
    main()
