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
c.execute('create table if not exists assessment (question_num int, exam1 int, exam2 int, distractors real, UNIQUE(question_num) ON CONFLICT REPLACE);')
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
	error = True
	exam = isInt(exam)
	try:
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
						error = False
					keyi = keyi + 1
					i = i + 1
					qnum = qnum + 1
	except:
		pass 	
	c.close()
	if error == True:
		return LoadZipGrade(filename, exam, conn)
	else:
		return error
	
def LoadZipGrade(filename, exam, conn):
	reader = csv.DictReader(open(os.path.abspath(os.path.expanduser(filename)), 'rU'))
	c = conn.cursor()
	error = True
	try:
		for row in reader:
			studentid = None
			zipgradeid = None
			externalid = None
			numquestions = None		
			
			for name in row.keys():
				if name.lower().strip() == 'zipgrade id':
					zipgradeid = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
				elif name.lower().strip() == 'external id' or name.lower().strip() == 'id' or name.lower().strip() == 'studentid' or name.lower().strip() == 'student id':
					externalid = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
				elif name.lower().strip() == 'num questions' or name.lower().strip() == 'num of questions' or name.lower().strip() == 'number of questions' or name.lower().strip() == 'number questions' or name.lower().strip() == 'questions':
					numquestions = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
			
			if externalid != None:
				studentid = externalid
			elif zipgradeid != None:
				studentid = zipgradeid
			else:
				return error
			
			if numquestions == None:
				numquestions = float('inf')
			
			for name in row.keys():
				answer = None
				questionfront = None
				questionback = None
				answer = None
				findqs = unicode(name.lower().strip(), "utf8")
				if len(findqs)>1:
					questionfront = findqs[0]
					if questionfront == "q":
						questionback = isInt(findqs[1:])
						if questionback != None and questionback > 0 and questionback <= numquestions:
							answer = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
							if answer in [0, 1] and exam != None and questionback != None and studentid != None:
								mylist = (exam, studentid, questionback, answer)
								c.execute('INSERT INTO questions (exam, id, question_num, correct) VALUES(?,?,?,?)',mylist)
								conn.commit()
								error = False
	except:
		pass
	return error
							

def BuildAssessment(conn):
	c = conn.cursor()
	error = True
	c.execute("SELECT DISTINCT pre.question_num AS num FROM questions AS pre JOIN questions AS post ON pre.question_num=post.question_num AND pre.id=post.id AND post.exam=2 WHERE pre.exam=1 ORDER BY pre.question_num ASC")
	results = c.fetchall()
	for row in results:
		mylist = (row[0], row[0], row[0], 4)
		c.execute('INSERT INTO assessment(exam1, exam2, question_num, distractors) VALUES(?,?,?,?)',mylist)
		conn.commit()
		error = False
	c.close()
	return error

def LoadAssessment(filename,conn,igroup=None):
	reader = csv.DictReader(open(os.path.abspath(os.path.expanduser(filename)), 'rU'))
	c = conn.cursor()
	error = True
	try:
		for row in reader:
			exam1 = None
			exam2 = None
			q = None
			qgroup = None
			distractors = None
			for name in row.keys():
				if name.lower().strip() == 'exam1' or name.lower().strip() == 'pretest' or name.lower().strip() == 'pre-test':
					exam1 = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
				elif name.lower().strip() == 'exam2' or name.lower().strip() == 'posttest' or name.lower().strip() == 'post-test':
					exam2 = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
				elif name.lower().strip() == 'q' or name.lower().strip() == 'question':
					q = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
				elif name.lower().strip() == 'group' or name.lower().strip() == 'groups':
					qgroup = unicode(str(row.get(name,'')).strip().lower(), "utf8")
				elif name.lower().strip() == 'options' or name.lower().strip() == 'answers' or name.lower().strip() == 'distractors' or name.lower().strip() == 'guess' or name.lower().strip() == 'guessing' or name.lower().strip() == 'probability':
					distractors = isFloat(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
					if distractors > 0 and distractors < 1:
						distractors = 1/distractors
			if exam1 != None and exam2 != None and q != None:
				mylist = (exam1, exam2, q, distractors)
				if igroup != None:
					qgroup = qgroup.replace(' ',',')
					qgroupList = qgroup.split(',')
					nqgroupList = [ isInt(x) for x in qgroupList ]
					if igroup in nqgroupList:
						c.execute('INSERT INTO assessment(exam1, exam2, question_num, distractors) VALUES(?,?,?,?)',mylist)
						error = False
				else:
					c.execute('INSERT INTO assessment(exam1, exam2, question_num, distractors) VALUES(?,?,?,?)',mylist)
					error = False
				conn.commit()
	except:
		pass
	c.close()
	return error



def LoadStudents(filename,conn):
	reader = csv.DictReader(open(os.path.abspath(os.path.expanduser(filename)), 'rU'))
	c = conn.cursor()
	error = True
	try:
		for row in reader:
			id = None
			for name in row.keys():
				if name.lower().strip() == 'id' or name.lower().strip() == 'studentid' or name.lower().strip() == 'student id':
					id = isInt(unicode(str(row.get(name,'')).strip().lower(), "utf8"))
			if id != None:
				mylist = (id,)
				c.execute('INSERT INTO student_list(id) VALUES(?)',mylist)
				conn.commit()
				error = False
	except:
		pass
	c.close()
	return error

def BuildStudents(conn):
	c = conn.cursor()
	error = True
	c.execute("SELECT DISTINCT pre.id AS id FROM questions AS pre JOIN questions AS post ON pre.question_num=post.question_num AND pre.id=post.id AND post.exam=2 WHERE pre.exam=1 ORDER BY pre.id ASC")
	results = c.fetchall()
	for row in results:
		mylist = (row[0],)
		c.execute('INSERT INTO student_list(id) VALUES(?)',mylist)
		conn.commit()
		error = False
	c.close()
	return error

def GenerateSelect(conn):
	c = conn.cursor()
	c.execute("SELECT firstResult.question_num AS q, firstResult.s AS Exam1, finalResult.s AS Exam2, firstResult.distractors AS d FROM (SELECT assessment.question_num, assessment.distractors, AVG(correct) As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1 GROUP BY questions.question_num) AS firstResult JOIN (SELECT assessment.question_num, AVG(correct) AS s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2 GROUP BY questions.question_num) AS finalResult ON firstResult.question_num=finalResult.question_num ORDER BY firstResult.question_num ASC")
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
		select = 'mytable.id AS id, mytable.Options AS Opts, COUNT(mytable.q) AS c'
		groupby = 'mytable.id, mytable.Options'
		cmTitle = 'id'
	else:
		select = 'mytable.q AS Q'
		groupby = 'mytable.q'
		cmTitle = 'Q'
	c.execute('SELECT ' + select + ', AVG(mytable.PL) AS PL FROM (SELECT pretest.id AS id, pretest.qn AS q, CASE WHEN pretest.s=0 THEN posttest.s ELSE 0 END AS PL, Options FROM (SELECT questions.id AS id, assessment.question_num AS qn, correct As s, assessment.distractors AS Options FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1) AS pretest JOIN (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2) AS posttest ON pretest.id=posttest.id AND pretest.qn=posttest.qn) AS mytable GROUP BY ' + groupby + ' ORDER BY ' + groupby)
	results = c.fetchall()
	dataset = []
	for row in results:
		dataset.append(row)
	c.close()
	if studentgroup==True:
		return pd.DataFrame(dataset,columns=(cmTitle, 'Options', 'Observations', 'PL'))
	else:
		return pd.DataFrame(dataset,columns=(cmTitle,'PL'))

def GenerateRL(conn, studentgroup=None):
	c = conn.cursor()
	if studentgroup==True:
		select = 'mytable.id AS id'
		groupby = 'mytable.id, mytable.Options'
		cmTitle = 'id'
	else:
		select = 'mytable.q AS Q'
		groupby = 'mytable.q'
		cmTitle = 'Q'
	c.execute('SELECT ' + select + ', AVG(mytable.RL) AS RL FROM (SELECT pretest.id AS id, pretest.qn AS q, CASE WHEN pretest.s=1 THEN posttest.s ELSE 0 END AS RL, Options FROM (SELECT questions.id AS id, assessment.question_num AS qn, correct As s, assessment.distractors AS Options FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1) AS pretest JOIN (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2) AS posttest ON pretest.id=posttest.id AND pretest.qn=posttest.qn) AS mytable GROUP BY ' + groupby + ' ORDER BY ' + groupby)
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
		groupby = 'mytable.id, mytable.Options'
		cmTitle = 'id'
	else:
		select = 'mytable.q AS Q'
		groupby = 'mytable.q'
		cmTitle = 'Q'
	c.execute('SELECT ' + select + ', AVG(mytable.ZL) AS ZL FROM (SELECT pretest.id AS id, pretest.qn AS q, CASE WHEN (pretest.s=0 AND posttest.s=0) THEN 1 ELSE 0 END AS ZL, Options FROM (SELECT questions.id AS id, assessment.question_num AS qn, correct As s, assessment.distractors AS Options FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1) AS pretest JOIN (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2) AS posttest ON pretest.id=posttest.id AND pretest.qn=posttest.qn) AS mytable GROUP BY ' + groupby + ' ORDER BY ' + groupby)
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
		groupby = 'mytable.id, mytable.Options'
		cmTitle = 'id'
	else:
		select = 'mytable.q AS Q'
		groupby = 'mytable.q'
		cmTitle = 'Q'
	c.execute('SELECT ' + select + ', AVG(mytable.NL) AS NL FROM (SELECT pretest.id AS id, pretest.qn AS q, CASE WHEN pretest.s=1 AND posttest.s=0 THEN 1 ELSE 0 END AS NL, Options FROM (SELECT questions.id AS id, assessment.question_num AS qn, correct As s, assessment.distractors AS Options FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam1 WHERE questions.exam=1) AS pretest JOIN (SELECT questions.id AS id, assessment.question_num AS qn, correct As s FROM questions JOIN student_list ON student_list.id=questions.id JOIN assessment ON questions.question_num=assessment.exam2 WHERE questions.exam=2) AS posttest ON pretest.id=posttest.id AND pretest.qn=posttest.qn) AS mytable GROUP BY ' + groupby + ' ORDER BY ' + groupby)
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
	numoptions = isFloat(x['Options'])
	if numoptions >= 1:
		egamma = (numoptions*(nl+pl*numoptions+rl-1))/((numoptions-1)**2)
		return egamma
	else:
		return None

def Mu(x):
	pl = x['PL']
	zl = x['ZL']
	rl = x['RL']
	nl = x['NL']
	numoptions = isFloat(x['Options'])
	if numoptions >= 1:
		emu = ((nl+rl)-1)/(numoptions-1)+nl+rl
		return emu
	else:
		return None

def Alpha(x):
	pl = x['PL']
	zl = x['ZL']
	rl = x['RL']
	nl = x['NL']
	numoptions = isFloat(x['Options'])
	if numoptions >= 1:
		ealpha = (numoptions*(nl*numoptions+pl+rl-1))/((numoptions-1)**2)
		return ealpha
	else:
		return None

def Flow(x):
	pl = x['PL']
	zl = x['ZL']
	rl = x['RL']
	nl = x['NL']
	numoptions = isFloat(x['Options'])
	if numoptions >= 1:
		eflow = (numoptions*(pl-nl))/(numoptions-1)
		return eflow
	else:
		return None

def AverageScores(x,totalobs,totalnonan):
	xpl = 0
	xrl = 0
	xnl = 0
	xzl = 0
	xg = 0
	xm = 0
	xa = 0
	xf = 0
	for i in range(0, len(x)):
		xpl = xpl + x.iloc[i]['PL']*(x.iloc[i]['Observations']/totalobs)
		xrl = xrl + x.iloc[i]['RL']*(x.iloc[i]['Observations']/totalobs)
		xnl = xnl + x.iloc[i]['NL']*(x.iloc[i]['Observations']/totalobs)
		xzl = xzl + x.iloc[i]['ZL']*(x.iloc[i]['Observations']/totalobs)
		if x.iloc[i]['Options'] > 0:
			xg = xg + x.iloc[i]['Gamma']*(x.iloc[i]['Observations']/totalnonan)
			xm = xm + x.iloc[i]['Mu']*(x.iloc[i]['Observations']/totalnonan)
			xa = xa + x.iloc[i]['Alpha']*(x.iloc[i]['Observations']/totalnonan)
			xf = xf + x.iloc[i]['Flow']*(x.iloc[i]['Observations']/totalnonan)
	return (xpl, xrl, xnl, xzl, xg, xm, xa, xf)

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
			e = LoadQuestions(os.path.abspath(os.path.expanduser(options.pretest.strip())),1,conn)
			if e == True:
				run = False
				print "The pretest file does not seem to follow a standard Scantron format."
		else:
			run = False
			print "The specified pretest file could not be found."
	else:
		run = False
		print "You must specify a pretest file."

	if len(options.posttest.strip()) > 0:
		if os.path.isfile(os.path.abspath(os.path.expanduser(options.posttest.strip()))) != False:
			e = LoadQuestions(os.path.abspath(os.path.expanduser(options.posttest.strip())),2,conn)
			if e == True:
				run = False
				print "The posttest file does not seem to follow a standard Scantron format."
		else:
			run = False
			print "The specified posttest file could not be found."
	else:
		run = False
		print "You must specify a posttest file."

	if len(options.students.strip()) > 0:
		if os.path.isfile(os.path.abspath(os.path.expanduser(options.students.strip()))) != False:
			e = LoadStudents(os.path.abspath(os.path.expanduser(options.students.strip())),conn)
			if e == True:
				run = False
				print "The student id list appears to be invalid."
		else:
			e = BuildStudents(conn)
			if e == True:
				run = False
				print "The specified student file could not be found."
			else:
				print "The student file could not be found, building id list from exams."
	else:
		e = BuildStudents(conn)
		if e == True:
			run = False
			print "You must specify a file containing a list of student IDs."
	
	if len(options.assessment.strip()) > 0:
		if os.path.isfile(os.path.abspath(os.path.expanduser(options.assessment.strip()))) != False:
			if options.group != None and options.group != False and len(str(options.group))>0:
				e = LoadAssessment(os.path.abspath(os.path.expanduser(options.assessment.strip())),conn, options.group)
			else:
				e = LoadAssessment(os.path.abspath(os.path.expanduser(options.assessment.strip())),conn)
			if e == True:
				run = False
				print "The assessment mapping file appears to be invalid."
		else:
			e = BuildAssessment(conn)
			if e == True:
				run = False
				print "The specified assessment file could not be found."
			else:
				print "The assessment file could not be found, assuming assessment question order match and n=4."
	else:
		e = BuildAssessment(conn)
		if e == True:
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
		equalLen = all(item == len(qoptions) for item in [len(pl),len(rl[['RL']]), len(zl[['ZL']]), len(nl[['NL']])])
		if equalLen != True or len(qoptions)<1:
			print "There is a mismatch between the question numbers specified in the assessment file and the number of questions in the exams.  Check to make sure you haven't mapped a single exam question to different assessment questions.  It is also possible to receive this error if one of the exam files does not conform to the standard Scantron format."
			sys.exit()
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
		overall = None
		overall = pd.concat([pl,rl[['RL']],zl[['ZL']],nl[['NL']],pt,pot,delta],axis=1)
		overall['Gamma'] = overall.apply(Gamma, axis=1)
		overall['Mu'] = overall.apply(Mu, axis=1)
		overall['Alpha'] = overall.apply(Alpha, axis=1)
		overall['Flow'] = overall.apply(Flow, axis=1)
		overall.to_csv('Walstad_Wagner_types_by_student_group.csv', index=False)
		studentidlist = overall.id.unique()
		olist=pd.DataFrame(columns=('id','PL','RL','ZL','NL','Gamma','Mu','Alpha','Flow','Observations','AdjustedObservations'))
		for sid in studentidlist:
			specst = overall[overall['id']==sid]
			specstnonan = specst[specst['Options']>0]
			totalobs = specst['Observations'].sum()
			totalobsnonan = specstnonan['Observations'].sum()
			xpl, xrl, xnl, xzl, xg, xm, xa, xf = AverageScores(specst,totalobs,totalobsnonan)
			rx = {'id':sid, 'PL':xpl, 'RL':xrl, 'ZL':xzl, 'NL':xnl, 'Gamma':xg, 'Mu':xm, 'Alpha':xa, 'Flow':xf, 'Observations':totalobs, 'AdjustedObservations':totalobsnonan}
			olist = olist.append(rx,ignore_index=True)
		pt = olist['RL'] + olist['NL']
		pot = olist['RL'] + olist['PL']
		delta = pot - pt
		pt = pd.DataFrame(pt,columns=('PreTest',))
		pot = pd.DataFrame(pot,columns=('PostTest',))
		delta = pd.DataFrame(delta,columns=('Delta',))
		overall = pd.concat([olist,pt,pot,delta],axis=1)
		overall.to_csv('Walstad_Wagner_types_by_student.csv', index=False)



if __name__ == '__main__':
	main()
