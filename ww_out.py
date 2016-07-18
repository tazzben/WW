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
c.execute('create table if not exists assessment (question_num int, exam1 int, exam2 int, UNIQUE(question_num) ON CONFLICT REPLACE);')
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
                if Key[keyi] == row[i]:
                    correct = 1
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

def LoadAssessment(filename,conn):
    reader = csv.DictReader(open(os.path.abspath(os.path.expanduser(filename)), 'rU'))
    c = conn.cursor()
    for row in reader:
        exam1 = None
        exam2 = None
        q = None
        for name in row.keys():
            if name.lower().strip() == 'exam1' or name.lower().strip() == 'pretest':
                exam1 = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
            elif name.lower().strip() == 'exam2' or name.lower().strip() == 'posttest':
                exam2 = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
            elif name.lower().strip() == 'q' or name.lower().strip() == 'question':
                q = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
        if exam1 != None and exam2 != None and q != None:
            mylist = (exam1, exam2, q)
            c.execute('INSERT INTO assessment(exam1, exam2, question_num) VALUES(?,?,?)',mylist)
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
    c.execute("SELECT firstResult.question_num AS q, firstResult.s AS Exam1, finalResult.s AS Exam2 FROM (SELECT assessment.question_num, AVG(correct) As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1 GROUP BY questions.question_num) AS firstResult JOIN (SELECT assessment.question_num, AVG(correct) AS s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2 GROUP BY questions.question_num) AS finalResult ON firstResult.question_num=finalResult.question_num")
    results = c.fetchall()
    dataset = []
    for row in results:
        dataset.append(row)
    c.close()
    return pd.DataFrame(dataset,columns=('Q','Exam1','Exam2'))

def GenerateStudentSelect(conn):
    c = conn.cursor()
    c.execute("SELECT firstResult.id, firstResult.s AS Exam1, finalResult.s AS Exam2 FROM (SELECT questions.id AS id, AVG(correct) As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1 GROUP BY questions.id) AS firstResult JOIN (SELECT questions.id AS id, AVG(correct) As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=2 GROUP BY questions.id) AS finalResult ON firstResult.id=finalResult.id ORDER BY finalResult.s DESC")
    results = c.fetchall()
    dataset = []
    for row in results:
        dataset.append(row)
    c.close()
    return pd.DataFrame(dataset,columns=('id','Exam1','Exam2'))

def GeneratePL(conn):
    c = conn.cursor()
    c.execute("SELECT mytable.q AS Q, AVG(mytable.PL) AS PL FROM (SELECT pretest.qn AS q, CASE WHEN pretest.s=0 THEN posttest.s ELSE 0 END AS PL FROM (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1) AS pretest JOIN (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2) AS posttest ON pretest.id=posttest.id AND pretest.qn=posttest.qn) AS mytable GROUP BY mytable.q ORDER BY mytable.q")
    results = c.fetchall()
    dataset = []
    for row in results:
        dataset.append(row)
    c.close()
    return pd.DataFrame(dataset,columns=('id','PL'))
    
def GenerateRL(conn):
    c = conn.cursor()
    c.execute("SELECT mytable.q AS Q, AVG(mytable.RL) AS RL FROM (SELECT pretest.qn AS q, CASE WHEN pretest.s=1 THEN posttest.s ELSE 0 END AS RL FROM (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1) AS pretest JOIN (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2) AS posttest ON pretest.id=posttest.id AND pretest.qn=posttest.qn) AS mytable GROUP BY mytable.q ORDER BY mytable.q")
    results = c.fetchall()
    dataset = []
    for row in results:
        dataset.append(row)
    c.close()
    return pd.DataFrame(dataset,columns=('id','RL'))

def GenerateZL(conn):
    c = conn.cursor()
    c.execute("SELECT mytable.q AS Q, AVG(mytable.ZL) AS ZL FROM (SELECT pretest.qn AS q, CASE WHEN (pretest.s=0 AND posttest.s=0) THEN 1 ELSE 0 END AS ZL FROM (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1) AS pretest JOIN (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2) AS posttest ON pretest.id=posttest.id AND pretest.qn=posttest.qn) AS mytable GROUP BY mytable.q ORDER BY mytable.q")
    results = c.fetchall()
    dataset = []
    for row in results:
        dataset.append(row)
    c.close()
    return pd.DataFrame(dataset,columns=('id','ZL'))

def GenerateNL(conn):
    c = conn.cursor()
    c.execute("SELECT mytable.q AS Q, AVG(mytable.NL) AS NL FROM (SELECT pretest.qn AS q, CASE WHEN pretest.s=1 AND posttest.s=0 THEN 1 ELSE 0 END AS NL FROM (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1) AS pretest JOIN (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2) AS posttest ON pretest.id=posttest.id AND pretest.qn=posttest.qn) AS mytable GROUP BY mytable.q ORDER BY mytable.q")
    results = c.fetchall()
    dataset = []
    for row in results:
        dataset.append(row)
    c.close()
    return pd.DataFrame(dataset,columns=('id','NL'))

def main():
    global conn
    desc = 'Calculate assessment data from Scantron format'
    p = optparse.OptionParser(description=desc)
    p.add_option('--pretest','-p', dest="pretest", help="Set pre-test file", default='', metavar='"<File Path>"')
    p.add_option('--posttest','-f', dest="posttest", help="Set post-test file", default='', metavar='"<File Path>"')
    p.add_option('--students','-s', dest="students", help="Set student ids file", default='', metavar='"<File Path>"')
    p.add_option('--assessment','-a', dest="assessment", help="Set assessment questions file", default='', metavar='"<File Path>"')

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
    
        pl = GeneratePL(conn)
        rl = GenerateRL(conn)
        zl = GenerateZL(conn)
        nl = GenerateNL(conn)
        overall = pd.concat([pl,rl[['RL']],zl[['ZL']],nl[['NL']]],axis=1)
        overall.to_csv('Walstad_Wagner_types.csv', index=False)
        questions.to_csv('Questions_output.csv', index=False)
        studentsSel.to_csv('Student_output.csv', index=False)
    

if __name__ == '__main__':
    main()