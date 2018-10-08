#!/usr/bin/env python
from __future__ import division, print_function, absolute_import
import argparse
import os
import platform
import sys
import codecs
import sqlite3
import csv
import pandas as pd
import webbrowser
from appJar import gui

pretestFile = ""
posttestFile = ""
assessmentFile = ""
studentsFile = ""
outputFolder = ""
app = None
conn = None

def DBSetup():
	global conn
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

def isAnswer(num):
	if num in ['',' ','a','b','c','d','e','x'] or isInt(num) != None:
		try:
			return int(round(float(num)))
		except:
			return 0
	else:
		return None

def altIsAnswer(num):
	return 1 if num in ['a', 'b', 'c', 'd', 'e'] else 0

def isReturnFile(myfile):
	if os.path.abspath(os.path.expanduser(myfile.strip())) != False:
		return os.path.abspath(os.path.expanduser(myfile.strip()))
	else:
		return 'You can\'t save to that location'

def LoadQuestions(filename, exam, conn):
	try:
		if sys.version_info[0] < 3:
			reader = csv.reader(open(os.path.abspath(os.path.expanduser(filename)), 'rU'))
		else:
			reader = csv.reader(open(os.path.abspath(os.path.expanduser(filename)), newline=''))
	except:
		return LoadZipGrade(filename, exam, conn)
	c = conn.cursor()
	Key = None
	error = True
	exam = isInt(exam)
	if exam != None:
		c.execute('DELETE FROM questions WHERE exam=?',(exam,))
		conn.commit()
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
	try:
		if sys.version_info[0] < 3:
			reader = csv.DictReader(open(os.path.abspath(os.path.expanduser(filename)), 'rU'))
		else:
			reader = csv.DictReader(open(os.path.abspath(os.path.expanduser(filename)), newline=''))
	except:
		return True
	c = conn.cursor()
	error = True
	alt_grading = False
	try:
		for row in reader:
			sid = None
			studentid = None
			zipgradeid = None
			externalid = None
			numquestions = None

			for name in list(row.keys()):
				if name.lower().strip() == 'zipgrade id':
					zipgradeid = isInt(str(str(row.get(name,'')).strip().lower()))
				elif name.lower().strip() == 'id' or name.lower().strip() == 'studentid' or name.lower().strip() == 'student id':
					sid = isInt(str(str(row.get(name,'')).strip().lower()))
				elif name.lower().strip() == 'external id' or name.lower().strip() == 'externalid':
					externalid = isInt(str(str(row.get(name,'')).strip().lower()))
				elif name.lower().strip() == 'num questions' or name.lower().strip() == 'num of questions' or name.lower().strip() == 'number of questions' or name.lower().strip() == 'number questions' or name.lower().strip() == 'questions':
					numquestions = isInt(str(str(row.get(name,'')).strip().lower()))
				elif name.lower().strip() == 'grade':
					alt_grading = True

			if externalid != None:
				studentid = externalid
			elif sid != None:
				studentid = sid
			elif zipgradeid != None:
				studentid = zipgradeid
			else:
				continue

			if numquestions == None:
				numquestions = float('inf')

			for name in list(row.keys()):
				answer = None
				questionfront = None
				questionback = None
				answer = None
				findqs = str(name.lower().strip())
				if len(findqs)>1:
					questionfront = findqs[0]
					if questionfront == "q":
						questionback = isInt(findqs[1:])
						if questionback != None and questionback > 0 and questionback <= numquestions:
							if alt_grading:
								answer = altIsAnswer(str(str(row.get(name, '')).strip().lower()))
							else:
								answer = isAnswer(str(str(row.get(name,'')).strip().lower()))
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
	try:
		if sys.version_info[0] < 3:
			reader = csv.DictReader(open(os.path.abspath(os.path.expanduser(filename)), 'rU'))
		else:
			reader = csv.DictReader(open(os.path.abspath(os.path.expanduser(filename)), newline=''))
	except:
		return True
	c = conn.cursor()
	c.execute('DELETE FROM assessment')
	conn.commit()
	error = True
	try:
		for row in reader:
			exam1 = None
			exam2 = None
			q = None
			qgroup = None
			distractors = None
			for name in list(row.keys()):
				if name.lower().strip() == 'exam1' or name.lower().strip() == 'pretest' or name.lower().strip() == 'pre-test':
					exam1 = isInt(str(str(row.get(name,'')).strip().lower()))
				elif name.lower().strip() == 'exam2' or name.lower().strip() == 'posttest' or name.lower().strip() == 'post-test':
					exam2 = isInt(str(str(row.get(name,'')).strip().lower()))
				elif name.lower().strip() == 'q' or name.lower().strip() == 'question':
					q = isInt(str(str(row.get(name,'')).strip().lower()))
				elif name.lower().strip() == 'group' or name.lower().strip() == 'groups':
					qgroup = str(str(row.get(name,'')).strip().lower())
				elif name.lower().strip() == 'options' or name.lower().strip() == 'answers' or name.lower().strip() == 'distractors' or name.lower().strip() == 'guess' or name.lower().strip() == 'guessing' or name.lower().strip() == 'probability' or name.lower().strip() == 'p':
					distractors = isFloat(str(str(row.get(name,'')).strip().lower()))
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
	try:
		if sys.version_info[0] < 3:
			reader = csv.DictReader(open(os.path.abspath(os.path.expanduser(filename)), 'rU'))
		else:
			reader = csv.DictReader(open(os.path.abspath(os.path.expanduser(filename)), newline=''))
	except:
		return True
	c = conn.cursor()
	c.execute('DELETE FROM student_list')
	conn.commit()
	error = True
	try:
		for row in reader:
			id = None
			for name in list(row.keys()):
				if name.lower().strip() == 'id' or name.lower().strip() == 'studentid' or name.lower().strip() == 'student id':
					id = isInt(str(str(row.get(name,'')).strip().lower()))
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
	numoptions = isFloat(x['Options']) if isFloat(x['Options']) != None else 0
	if numoptions > 1:
		egamma = (numoptions*(nl+pl*numoptions+rl-1))/((numoptions-1)**2)
		return egamma
	else:
		return None

def Mu(x):
	pl = x['PL']
	zl = x['ZL']
	rl = x['RL']
	nl = x['NL']
	numoptions = isFloat(x['Options']) if isFloat(x['Options']) != None else 0
	if numoptions > 1:
		emu = ((nl+rl)-1)/(numoptions-1)+nl+rl
		return emu
	else:
		return None

def Alpha(x):
	pl = x['PL']
	zl = x['ZL']
	rl = x['RL']
	nl = x['NL']
	numoptions = isFloat(x['Options']) if isFloat(x['Options']) != None else 0
	if numoptions > 1:
		ealpha = (numoptions*(nl*numoptions+pl+rl-1))/((numoptions-1)**2)
		return ealpha
	else:
		return None

def Flow(x):
	pl = x['PL']
	zl = x['ZL']
	rl = x['RL']
	nl = x['NL']
	numoptions = isFloat(x['Options']) if isFloat(x['Options']) != None else 0
	if numoptions > 1:
		eflow = (numoptions*(pl-nl))/(numoptions-1)
		return eflow
	else:
		return None

def Gain(x):
	gamma = x['Gamma']
	mu = x['Mu']
	if gamma != None and mu != None and ((1-mu) != 0):
		return gamma/(1-mu)
	else:
		return None

def GainZero(x):
	pl = x['PL']
	rl = x['RL']
	nl = x['NL']
	if (1-nl-rl) > 0:
		return (pl-nl)/(1-nl-rl)
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
	xga = 0
	xgaz = 0
	for i in range(0, len(x)):
		xpl = xpl + x.iloc[i]['PL']*(x.iloc[i]['Observations']/totalobs)
		xrl = xrl + x.iloc[i]['RL']*(x.iloc[i]['Observations']/totalobs)
		xnl = xnl + x.iloc[i]['NL']*(x.iloc[i]['Observations']/totalobs)
		xzl = xzl + x.iloc[i]['ZL']*(x.iloc[i]['Observations']/totalobs)
		xgaz = xgaz + x.iloc[i]['GammaGainZero']*(x.iloc[i]['Observations']/totalobs)
		internalNumOptions = x.iloc[i]['Options'] if x.iloc[i]['Options'] != None else 0
		if internalNumOptions > 0:
			xg = xg + x.iloc[i]['Gamma']*(x.iloc[i]['Observations']/totalnonan)
			xm = xm + x.iloc[i]['Mu']*(x.iloc[i]['Observations']/totalnonan)
			xa = xa + x.iloc[i]['Alpha']*(x.iloc[i]['Observations']/totalnonan)
			xf = xf + x.iloc[i]['Flow']*(x.iloc[i]['Observations']/totalnonan)
			xga = xga + x.iloc[i]['GammaGain']*(x.iloc[i]['Observations']/totalnonan)
	return (xpl, xrl, xnl, xzl, xg, xm, xa, xf, xga, xgaz)

def RunCalc():
	global conn
	global pretestFile
	global posttestFile
	global assessmentFile
	global studentsFile
	global outputFolder
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
		return "There is a mismatch between the question numbers specified in the assessment file and the number of questions in the exams.  Check to make sure you haven't mapped a single exam question to different assessment questions.  It is also possible to receive this error if one of the exam files does not conform to the standard Scantron or ZipGrader format."
	overall = pd.concat([pl,rl[['RL']],zl[['ZL']],nl[['NL']],pt,pot,delta,qoptions],axis=1)
	overall['Gamma'] = overall.apply(Gamma, axis=1)
	overall['Mu'] = overall.apply(Mu, axis=1)
	overall['Alpha'] = overall.apply(Alpha, axis=1)
	overall['Flow'] = overall.apply(Flow, axis=1)
	overall['GammaGain'] = overall.apply(Gain, axis=1)
	overall['GammaGainZero'] = overall.apply(GainZero, axis=1)
	del questions['Options']
	del overall['Options']
	try:
		overall.to_csv(os.path.join(outputFolder,'Walstad_Wagner_types.csv'), index=False)
		questions.to_csv(os.path.join(outputFolder,'Questions_output.csv'), index=False)
		studentsSel.to_csv(os.path.join(outputFolder,'Student_output.csv'), index=False)
	except:
		return "Something went wrong when trying to write the files to disk."
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
	overall['GammaGain'] = overall.apply(Gain, axis=1)
	overall['GammaGainZero'] = overall.apply(GainZero, axis=1)
	try:
		overall.to_csv(os.path.join(outputFolder,'Walstad_Wagner_types_by_student_group.csv'), index=False)
	except:
		return "Something went wrong when trying to write the files to disk."
	studentidlist = overall.id.unique()
	olist=pd.DataFrame(columns=('id','PL','RL','ZL','NL','Gamma','Mu','Alpha','Flow','Observations','AdjustedObservations'))
	for sid in studentidlist:
		specst = overall[overall['id']==sid]
		specstnonan = specst[specst['Options']>0]
		totalobs = specst['Observations'].sum()
		totalobsnonan = specstnonan['Observations'].sum()
		xpl, xrl, xnl, xzl, xg, xm, xa, xf, xga, xgaz = AverageScores(specst,totalobs,totalobsnonan)
		rx = {'id':sid, 'PL':xpl, 'RL':xrl, 'ZL':xzl, 'NL':xnl, 'Gamma':xg, 'Mu':xm, 'Alpha':xa, 'Flow':xf, 'Observations':totalobs, 'AdjustedObservations':totalobsnonan, 'GammaGain':xga, 'GammaGainZero':xgaz}
		olist = olist.append(rx,ignore_index=True)
	pt = olist['RL'] + olist['NL']
	pot = olist['RL'] + olist['PL']
	delta = pot - pt
	pt = pd.DataFrame(pt,columns=('PreTest',))
	pot = pd.DataFrame(pot,columns=('PostTest',))
	delta = pd.DataFrame(delta,columns=('Delta',))
	overall = pd.concat([olist,pt,pot,delta],axis=1)
	try:
		overall.to_csv(os.path.join(outputFolder,'Walstad_Wagner_types_by_student.csv'), index=False)
	except:
		return "Something went wrong when trying to write the files to disk."
	return True

def ProcessInterface():
	global conn
	global pretestFile
	global posttestFile
	global assessmentFile
	global studentsFile
	global outputFolder
	run = True
	if len(pretestFile.strip()) > 0:
		if os.path.isfile(os.path.abspath(os.path.expanduser(pretestFile.strip()))) != False:
			e = LoadQuestions(os.path.abspath(os.path.expanduser(pretestFile.strip())),1,conn)
			if e == True:
				run = False
				return "The pre-test file does not seem to follow a standard Scantron or ZipGrade format."
		else:
			run = False
			return "The specified pre-test file could not be found."
	else:
		run = False
		return "You must specify a pre-test file."

	if len(posttestFile.strip()) > 0:
		if os.path.isfile(os.path.abspath(os.path.expanduser(posttestFile.strip()))) != False:
			e = LoadQuestions(os.path.abspath(os.path.expanduser(posttestFile.strip())),2,conn)
			if e == True:
				run = False
				return "The post-test file does not seem to follow a standard Scantron or ZipGrade format."
		else:
			run = False
			return "The specified post-test file could not be found."
	else:
		run = False
		return "You must specify a post-test file."

	if len(studentsFile.strip()) > 0:
		if os.path.isfile(os.path.abspath(os.path.expanduser(studentsFile.strip()))) != False:
			e = LoadStudents(os.path.abspath(os.path.expanduser(studentsFile.strip())),conn)
			if e == True:
				run = False
				return "The student id list appears to be invalid."
		else:
			e = BuildStudents(conn)
			if e == True:
				run = False
				return "The specified student file could not be found."
	else:
		e = BuildStudents(conn)
		if e == True:
			run = False
			return "You must specify a file containing a list of student IDs."

	if len(assessmentFile.strip()) > 0:
		if os.path.isfile(os.path.abspath(os.path.expanduser(assessmentFile.strip()))) != False:
			e = LoadAssessment(os.path.abspath(os.path.expanduser(assessmentFile.strip())),conn)
			if e == True:
				run = False
				return "The assessment mapping file appears to be invalid."
		else:
			e = BuildAssessment(conn)
			if e == True:
				run = False
				return "The specified assessment file could not be found."
	else:
		e = BuildAssessment(conn)
		if e == True:
			run = False
			return "You must specify an assessment mapping file."

	if len(outputFolder.strip()) > 0:
		if os.path.isdir(os.path.abspath(os.path.expanduser(outputFolder.strip()))) != True:
			run = False
			return "The output folder appears to be invalid."
	else:
		run = False
		return "You must specify an output folder."
	return run

def press(button):
	global app
	if button == "Quit":
		app.stop()
	else:
		app.hideButton("Run")
		app.hideButton("Quit")
		processRun()
		app.showButton("Run")
		app.showButton("Quit")

def processRun():
	global app
	global conn
	DBSetup()
	result = ProcessInterface()
	if result == True:
		rc = RunCalc()
		if rc == True:
			app.infoBox('Success', "The requested files have been generated!")
		else:
			if len(str(rc))>1:
				wrn = str(rc)
			elif len(str(result))>1:
				wrn = str(result)
			else:
				wrn = "Something went wrong when calculating the results.  Make sure all of your files conform to the required format."
			app.warningBox('Output File Error', wrn)
	else:
		app.warningBox('Input File Error', result)
	conn.close()


def openDir(button):
	global outputFolder
	global app
	f = app.directoryBox(title=None, dirName=None)
	if f != None:	
		f = '' if f == '' else os.path.abspath(os.path.expanduser(f))
	else:
		f = ''
	if os.path.isdir(f) or f=='':
		outputFolder = f
		app.setLabel("save", outputFolder)


def pFile(button):
	global pretestFile
	global posttestFile
	global assessmentFile
	global studentsFile
	global app
	f = app.openBox(title=None, dirName=None, fileTypes=[('CSV', '*.csv'),], asFile=False)
	if f != None:
		f = '' if f == '' else os.path.abspath(os.path.expanduser(f))
	else:
		f = ''
	if os.path.isfile(f) or f=='':
		if button == 'Pre-test' and f != None:
			pretestFile = f
			app.setLabel("preTest", pretestFile)
		elif button == 'Post-test' and f != None:
			posttestFile = f
			app.setLabel("postTest", posttestFile)
		elif button == 'Assessment Map' and f != None:
			assessmentFile = f
			app.setLabel("ament", assessmentFile)
		elif button == 'List of Students' and f != None:
			studentsFile = f
			app.setLabel("stud", studentsFile)

def isCSV(f):
	filename, file_extension = os.path.splitext(f)
	if file_extension.lower().strip() == '.csv':
		return True
	else:
		return False

def preTestDrop(f):
	global pretestFile
	global app
	f = '' if f == '' else os.path.abspath(os.path.expanduser(f))
	if (os.path.isfile(f) or f=='') and f != None:
		if isCSV(f):
			pretestFile = f
			app.setLabel("preTest", pretestFile)

def postTestDrop(f):
	global posttestFile
	global app
	f = '' if f == '' else os.path.abspath(os.path.expanduser(f))
	if (os.path.isfile(f) or f=='') and f != None:
		if isCSV(f):
			posttestFile = f
			app.setLabel("postTest", posttestFile)

def assessmentDrop(f):
	global assessmentFile
	global app
	f = '' if f == '' else os.path.abspath(os.path.expanduser(f))
	if (os.path.isfile(f) or f=='') and f != None:
		if isCSV(f):
			assessmentFile = f
			app.setLabel("ament", assessmentFile)
			
def studentsDrop(f):
	global studentsFile
	global app
	f = '' if f == '' else os.path.abspath(os.path.expanduser(f))
	if (os.path.isfile(f) or f=='') and f != None:
		if isCSV(f):
			studentsFile = f
			app.setLabel("stud", studentsFile)

def outputFolderDrop(f):
	global outputFolder
	global app
	f = '' if f == '' else os.path.abspath(os.path.expanduser(f))
	if (os.path.isdir(f) or f=='') and f != None:
		outputFolder = f
		app.setLabel("save", outputFolder)

def menuPress(menu):
	global app
	url = ''
	if menu == 'Quit':	
		app.stop()
	elif menu == 'Open online instructions':
		url = 'https://tazzben.github.io/WW/'
	elif menu == 'Download example files':
		url = 'http://downloads.bensresearch.com/ww_data.zip'
	elif menu == 'E-Mail for help':
		url = 'mailto:bosmith@unomaha.edu?subject=Help with Assessment Disaggregation'
	if len(url)>0:
		if sys.platform.startswith('darwin'):
			try:
				browser = webbrowser.get("safari")
				browser.open_new_tab(url)
			except:
				app.warningBox('Browser Error', 'Unfortunately, I could not open the default browser on your system.  You can find the help resources at https://tazzben.github.io/WW/.')
		else:
			try:			
				webbrowser.get().open_new_tab(url)
			except:
				try:
					webbrowser.open(url)
				except:
					app.warningBox('Browser Error', 'Unfortunately, I could not open the default browser on your system.  You can find the help resources at https://tazzben.github.io/WW/.')

def showMessage(label,text):
	global app
	app.setLabel(label,text)

def main():
	global conn
	global app
	global pretestFile
	global posttestFile
	global assessmentFile
	global studentsFile
	global outputFolder
	scantronText = "A CSV file in Scantron or ZipGrader format.  More details online (under 'Help')."
	assessmentText = "A CSV file with following columns: 'Q', 'Exam1', 'Exam2', and 'Options'. More details online (under 'Help')."
	studentsText = "A CSV file with a column named 'id'; used to assess a subset of the class. More details online (under 'Help')."
	
	outputText = "The output folder for all generated files."
	app = gui("Disaggregate and Adjust Value-added Learning Scores", "1000x300", useTtk=True)
	app.setResizable(canResize=False)
	if getattr(sys, 'frozen', False):
  		bundle_dir = sys._MEIPASS
	else:
  		bundle_dir = os.path.dirname(os.path.abspath(__file__))
	if sys.platform.startswith('win32'):
		osicon = os.path.join(bundle_dir,"icon.ico")
	elif sys.platform.startswith('linux'):
		osicon = os.path.join(bundle_dir,"icon.gif")
	else:
		osicon = ''
	if len(osicon)>0 and os.path.isfile(osicon) != False:
		app.setIcon(osicon)
	fileMenus = ["Quit",]
	helpMenus = ["Open online instructions","Download example files","E-Mail for help"]
	app.addMenuList("File", fileMenus, menuPress)
	app.addMenuList("Help", helpMenus, menuPress)
		
	app.startLabelFrame("Required Files")
	
	app.addButton("Pre-test", pFile, 0, 0)
	app.addLabel("preTest","",0,1)
	app.setButtonOverFunction("Pre-test", [lambda x: showMessage("preTest", scantronText), lambda x: showMessage("preTest", pretestFile)])
	
	app.addButton("Post-test", pFile, 1, 0)
	app.addLabel("postTest","",1,1)
	app.setButtonOverFunction("Post-test", [lambda x: showMessage("postTest", scantronText), lambda x: showMessage("postTest", posttestFile)])
	app.stopLabelFrame()

	app.startLabelFrame("Optional Files")
	app.addButton("Assessment Map", pFile, 2, 0)
	app.addLabel("ament","",2,1)
	app.setButtonOverFunction("Assessment Map", [lambda x: showMessage("ament", assessmentText), lambda x: showMessage("ament", assessmentFile)])
	
	app.addButton("List of Students", pFile, 3, 0)
	app.addLabel("stud","",3,1)
	app.setButtonOverFunction("List of Students", [lambda x: showMessage("stud", studentsText), lambda x: showMessage("stud", studentsFile)])

	app.stopLabelFrame()
	app.startLabelFrame("Output Location")
	app.addButton("Save Location", openDir, 4, 0)
	app.addLabel("save","",4,1)
	app.setButtonOverFunction("Save Location", [lambda x: showMessage("save", outputText), lambda x: showMessage("save", outputFolder)])

	try:
		app.setLabelDropTarget("preTest", preTestDrop, False)
		app.setLabelDropTarget("postTest", postTestDrop, False)
		app.setLabelDropTarget("ament", assessmentDrop, False)
		app.setLabelDropTarget("stud", studentsDrop, False)
		app.setLabelDropTarget("save", outputFolderDrop, False)
	except:
		pass
				
	app.addButtons(["Run", "Quit"], press, colspan=2)
	app.stopLabelFrame()
	app.go()

if __name__ == '__main__':
	main()
