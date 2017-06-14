#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        deryann  Mongo DB
# Purpose:
#
# Author:      user
#
# Created:     09/05/2017
# Copyright:   (c) user 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from pymongo import MongoClient
import pymongo
import codecs
from HDYLatexParser import HDYLatexParser
import os,sys
import difflib

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def getDefaultDB():

    import configparser
    Config = configparser.ConfigParser()
    Config.read("PyMongoDB.ini")
    strURL = Config.get("DBConnectionInfo","DBURL")
    nPort = Config.getint("DBConnectionInfo","DBPORT")
    strDBNAME = Config.get("DBConnectionInfo","DBNAME")
    strAUTHNAME = Config.get("DBConnectionInfo","DBAUTHNAME")
    strAUTHPWD = Config.get("DBConnectionInfo","DBAUTHPWD")

    connection = MongoClient(strURL, nPort)
    db = connection[strDBNAME]
    db.authenticate(strAUTHNAME, strAUTHPWD)
    return db

def getDefaultCollect():
    db= getDefaultDB()
    collect = db['testtable']
    return collect
    pass

def showAllData():
    collect = getDefaultCollect()
    for post in collect.find({'qtag':'微分'}):
        print (post)
    pass

def addDataIntoCollect():
    collect = getDefaultCollect()
    dicInsertItem = {
        "fulldoc": 'Question 100 {} ', 'qtag':['B6C2', '微分']
        }
    result = collect.insert_one(dicInsertItem)
    print (result.inserted_id)

def removeInCollect():
    collect = getDefaultCollect()
    print( "Original Count : %d",collect.count())
    result = collect.delete_many ({'qtag':'微分'})
    print( "NOW Count :%d",collect.count())
    print( "Write result:")
    print(result)

def moveDataIntoMongoDB():
    collect = getDefaultCollect()
    latexFile = HDYLatexParser("QSingleChoice.tex")
    latexFile.runReport()
    numTotal = latexFile.getCountOfQ()
    if numTotal == 0 :
        return
    lstInsert = [latexFile.getQuestionInJSONMode(i) for i in range(numTotal)]
    result = collect.insert_many(lstInsert)
    print (result.inserted_ids)

def moveDataIntoMongoDBByFile(strInputFile):
    collect = getDefaultCollect()
    latexFile = HDYLatexParser(strInputFile)
    latexFile.runReport()
    numTotal = latexFile.getCountOfQ()
    if numTotal == 0 :
        return
    lstInsert = [latexFile.getQuestionInJSONMode(i) for i in range(numTotal)]
    result = collect.insert_many(lstInsert)
    print (result.inserted_ids)


def isQStartLine(strTest):
    if u"\\begin{QUESTION}" in strTest:
        return True
    return False

def isQEndLine(strTest):
    if u"\end{QUESTION}" in strTest:
        return True
    return False

def isComment(strTest):
    if strTest==None:
        return False
    elif len(strTest)==0:
        return False
    elif strTest[0]=='%':
        return True
    else:
        return False
    return False

def isQuestionsFile(strFileName):
    bQuestionFile = False
    while True:
        try:
            fPt = codecs.open( strFileName, "r", "utf-8" )
            ptFileStart =fPt.tell()

            print("Open file OK!!")
            fPt.seek(ptFileStart, os.SEEK_SET)

            strAllLines = fPt.readlines()

            for index in range(len(strAllLines)):
                if isComment(strAllLines[index]):
                    pass
                elif isQStartLine(strAllLines[index]):
                    bQuestionFile=True
                    break
            break
        except (IOError, UnicodeDecodeError):
            print ("Error")
            break
    return bQuestionFile

def runAllTexFile():
    from fnmatch import fnmatch
    root =u"E:\\NCTUG2"
    pattern = "*.tex"
    strOutputFileName = u"WannaGetQList.txt"
    fPtOutput = codecs.open(strOutputFileName, "w+", "utf-8" )
    for path, subdirs, files in os.walk(root):
        for name in files:
            if fnmatch(name, pattern):
                print (os.path.join(path, name))
                if isQuestionsFile(os.path.join(path, name)):
                    print (os.path.join(path, name) + " is QFile!!")
                    fPtOutput.write(os.path.join(path, name)  +os.linesep)
    fPtOutput.close()
    pass

def moveDataIntoMongoDBForAllWannaList():
    collect = getDefaultCollect()
    strFileName = u"WannaGetQList.txt"
    fPt = codecs.open( strFileName, "r", "utf-8" )
    strAllLines = fPt.read().splitlines()

    for index in range(len(strAllLines)):
        latexFile = HDYLatexParser(strAllLines[index])
        print("[Move "+strAllLines[index]+" to DB]")
        latexFile.runReport()
        numTotal = latexFile.getCountOfQ()
        if numTotal == 0 :
            return
        lstInsert = [latexFile.getQuestionInJSONMode(i) for i in range(numTotal)]
        result = collect.insert_many(lstInsert)
        print (result.inserted_ids)

def cloneDataIntoValidQS():
    db=getDefaultDB()
    collect = db['testtable']
    collect2 = db['validqs']
    k =0
    result = collect2.insert_many( collect.find({
                                "QBODY": {
                                    "$ne": ""
                                },
                                "QSOL": {
                                    "$ne": ""
                                }}))
    print (collect2.count())

def isSameString(str1,str2):
    if str1 == str2:
        return true
    import re
    skipblank = re.compile(r'\s+')
    return skipblank.sub('', str1) == skipblank.sub('', str2)

def isDuplicatedDoc(doc1, doc2):
    bDuplicated = True
    if isSameString (doc1["QBODY"] , doc2["QBODY"] ) and isSameString (doc1["QANS"] , doc2["QANS"]) and isSameString (doc1["QSOL"], doc2["QSOL"]) :
        if isSameString(doc1["FULLDOC"], doc2["FULLDOC"]):
            return True
    return False

def countSameAsZero(docs):
    nCount = 0
    if docs.count() >=1:
        doc=docs[0]
        for i in range(docs.count()):
            if isDuplicatedDoc(doc, docs[i]):
                nCount+=1
    return nCount

def runGroupProcessToAddIntoCleanqs(docs, collect):
    if docs.count() >=1:
        doc=docs[0]
        collect.insert_one(doc)
    return

def getIDInToList (docs):
    lst = []
    for doc in docs:
        lst.append(doc["_id"])
    return lst

def runNonGroupProcessToAddIntoLog(docs,collect):
    lst = getIDInToList (docs)
    dic = {"QSet":lst}
    collect.insert_one(dic)
    return


def searchDistinct():
    """
    整理不同的validqs 裡面的資料，
    利用QBODY 做資料群組
    若是主要資料完全相同者，合併記錄至 cleanqs
    若是有主要資料有部分不同者，紀錄至有關係群組裡
    """
    db=getDefaultDB()
    collect2 = db['validqs']
    collect3 = db['cleanqs']
    collect4 = db['relateionship']
    lst = collect2.distinct("QBODY")
    print (len(lst))
    nCountDistinctQBODY = len(lst)
    nCountCanGroup = 0
    nCountCanNOTGroup = 0
    for i in range(nCountDistinctQBODY): ###{0,1,2}:
        #print ("i=",i)
        #print(lst[i])
        findstring= {"QBODY": lst[i] }
        docs=collect2.find(findstring)
        #print("Same data count:",docs.count())

        nCount = countSameAsZero(docs)
        if nCount == docs.count():
            #It mean OK to group as one!
            #print ("Groped as one!!!!! ")
            runGroupProcessToAddIntoCleanqs(docs,collect3)
            nCountCanGroup+=1
        else:
            #print ("Oh No they cannot Groped as one!!!!! ")
            runNonGroupProcessToAddIntoLog(docs,collect4)
            nCountCanNOTGroup+=1
        #print("===========================")
    print ("Can Group count " , nCountCanGroup)
    print ("Can NOT Group count " , nCountCanNOTGroup)

def findSomeQIntoFile(collect, dicfinding, strOutputFileName):
    docs = collect.find(dicfinding)
    fPtOutput = codecs.open(strOutputFileName, "w+", "utf-8" )

    for doc in docs.sort([("SuggestQusetionStyle",pymongo.ASCENDING),("FULLDOC",pymongo.ASCENDING)] ):
        fPtOutput.write(doc["FULLDOC"])

    fPtOutput.close()
    pass

def saveSomeRegexDataIntoFile(strRegex, strFileName):
    db = getDefaultDB()
    collect3 = db['cleanqs']
    dicfinding ={
    "$or": [
        {
            "FULLDOC": {
                "$regex":strRegex
            }
        }
    ]
    }
    findSomeQIntoFile(collect3, dicfinding,strFileName)
    pass


def runFindSomeDataIntoFile():
#    strReg=".*(拋物線|橢圓|雙曲線|二次曲線).*"
#    fileName = "TEST.tex"
    strReg=".*(lvec|空間中|空間坐標|向量).*"
    fileName = "Space.tex"

    saveSomeRegexDataIntoFile(strReg,fileName)


def findQById(inputId, collect):
    dic = {"_id": inputId}
    return collect.find_one(dic)

def reportQuestionsDiffence():
    db = getDefaultDB()
    collect2 = db['validqs']
    collect3 = db['cleanqs']
    collect4 = db['relateionship']
    docs = collect4.find({})
    for k in {0,1,2}: #in docs:
        doc = docs[k]
        lst =  doc["QSet"]
        if len(lst)>1:
            id0 = lst[0]
            id1 = lst[1]
            q0 = findQById(id0, collect2)
            q1 = findQById(id1, collect2)
            text1_lines=q0["FULLDOC"].splitlines()
            text2_lines=q1["FULLDOC"].splitlines()
            d = difflib.Differ(charjunk=difflib.IS_CHARACTER_JUNK)
            print (k)
            print ("=================================")
            #diff = d.compare(text1_lines, text2_lines)
            #print ('\n'.join(diff))
            #print ("=================================")
            diff = difflib.context_diff(text1_lines, text2_lines)
            print ('\n'.join(diff))
            print ("=================================")
    pass

QUESTION_STYLE_UNKNOWN = 0              #未知
QUESTION_STYLE_SINGLE_CHOICE = 1        #單選
QUESTION_STYLE_MULTIPLE_CHOICES = 2     #多選
QUESTION_STYLE_CHOICE_BLANK = 3         #選填 (可畫卡的填充題)
QUESTION_STYLE_BLANK = 4                #填充
QUESTION_STYLE_CAL = 5                #計算證明題

def updateQuestionsStyle():
    """
    依據幾個QUSETION 內的規則，猜測出題型
    """
    db = getDefaultDB()
    collect3 = db['cleanqs']

    #填充題規則(先比對好簡單的填充題規則，未來會被其他題型給複寫)
    dicFinding={"FULLDOC": {
                                    "$regex": ".*(originalAnsBox).*"
                                }
               }

    dicUpdate = {'$set':{"SuggestQusetionStyle": QUESTION_STYLE_BLANK}}
    result = collect3.update_many(dicFinding, dicUpdate)
    print ("result.matched_count Of QS ",QUESTION_STYLE_BLANK," =", result.matched_count)

    #選填題規則
    dicFinding={
                "$and": [
                            {
                                "FULLDOC": {
                                    "$regex": ".*(TCNBOX).*"
                                }
                            }
                        ]
                    }
    dicUpdate = {'$set':{"SuggestQusetionStyle": QUESTION_STYLE_CHOICE_BLANK}}
    result = collect3.update_many(dicFinding,dicUpdate)
    print ("result.matched_count Of QS ",QUESTION_STYLE_CHOICE_BLANK," =", result.matched_count)

    #單擇題規則
    dicFinding={
                "$and": [
                            {
                                "FULLDOC": {
                                    "$regex": ".*(QOPS|QOPSINONELINE).*"
                                },
                                "QANS": {
                                    "$in": [
                                        "(1)",
                                        "(2)",
                                        "(3)",
                                        "(4)",
                                        "(5)"
                                    ]
                                }
                            }
                        ]
                    }
    dicUpdate = {'$set':{"SuggestQusetionStyle": QUESTION_STYLE_SINGLE_CHOICE}}
    result = collect3.update_many(dicFinding,dicUpdate)
    print ("result.matched_count Of QS ",QUESTION_STYLE_SINGLE_CHOICE," =", result.matched_count)

    #多選題規則
    dicFinding={
                "$and": [
                            {
                                "FULLDOC": {
                                    "$regex": ".*(QOPS|QOPSINONELINE).*"
                                },
                                "QANS": {
                                    "$not":{
                                        "$in": [
                                            "(1)",
                                            "(2)",
                                            "(3)",
                                            "(4)",
                                            "(5)"
                                                ]
                                        }
                                }
                            }
                        ]
                    }

    dicUpdate = {'$set':{"SuggestQusetionStyle": QUESTION_STYLE_MULTIPLE_CHOICES}}
    result = collect3.update_many(dicFinding,dicUpdate)
    print ("result.matched_count Of QS ",QUESTION_STYLE_MULTIPLE_CHOICES," =", result.matched_count)



def updateQuestions():
    updateQuestionsStyle()

def main():

#    removeInCollect()
#    moveDataIntoMongoDB()

    #列出所有子目檔案有*.tex者
#    runAllTexFile()
#    moveDataIntoMongoDBForAllWannaList()
#    moveDataIntoMongoDBByFile("E:\\NCTUG2\\陳立班務考卷\\高中部\\105(2016)學年度班系\\豐原2H\\下學期\\小考卷\\02\\QSingleChoice.tex")
    #將合法的dataclone 到 validqs 去
#    cloneDataIntoValidQS()

    #練習查詢 'distinct' 並將一系列的考Group整理成一個，剩餘的記錄其可能關係
    import timeit
    timer_start = timeit.default_timer()


    #searchDistinct()
    #reportQuestionsDiffence()
    runFindSomeDataIntoFile()
    #updateQuestions()

    timer_end = timeit.default_timer()
    print("Time usage:",timer_end - timer_start," sec(s)")
    pass

if __name__ == '__main__':
    main()
