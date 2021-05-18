import telegramModule
import os
import sys
import time
import json
from bs4 import BeautifulSoup
import requests
from datetime import date
from datetime import timedelta
import sqlite3

# 휴가자를 얻을수 있는 URL
VacationDetailURL = os.environ.get("VACATION_URL_FOR_HIWORKS_NOTI")


# 환경설정 파일 읽기.
exefilePath = os.path.dirname(sys.argv[0])
dbFile = exefilePath+'/holyday.db'

# 텔래그램 아이디를 가지고 오자.
notiGroupTelegramId = os.environ.get("TELEGRAM_ID_OF_ADMIN_FOR_HIWORKS_NOTI")


# 세션 아이디를 가지고 오자. 
sessionid = os.environ.get("SESSION_ID_FOR_HIWORKS_NOTI")


#리퀘스트 해더.
requestHeader = {"Cookie": "PHPSESSID={0};".format(sessionid),
             "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
             "Content-Type": "application/x-www-form-urlencoded"
             }

# 휴가자 리스트를 얻어와서 전달하는 함수. 파라메터를 던지지 않아서 오늘날짜의 휴가자만 가지고 온다. 사용하지 않음.
def getList():

    r = requests.get(
            url=VacationDetailURL,
            headers=requestHeader
        )

    data = json.loads(r.text)

    if "resultCode" in data:
        if data.get("resultCode") != "SUCCESS":
            return ""
        resultTable = data.get("result")
        totalCount = data.get("totalCount")
        month = data.get("month")
        day = data.get("day")
        soup = BeautifulSoup(resultTable, 'html.parser')

        if int(totalCount) < 1:
            return ""

        resultString = "{0} {1} 총 휴가자 {2}명 내역입니다. \n".format(month,day,totalCount)


        userList = soup.find_all('tr')
        for tags in userList:
            ud = tags.find_all('td')
            s = "{0} {1} : {2} \n".format(ud[1].text,ud[0].text, ud[3].text)
            # 0 이름 1 부서 2 연차(일차) 3 결제중
            resultString += s
            
            


        telegramModule.sendMessage(notiGroupTelegramId, resultString)


# 목표날의 휴가자를 모두 가져오는 함수.
# 리턴값은 아래와 같다. 
# (total 총 휴가자, month 월, day 일 , userStringList 사용자의 리스트)
def getTargetDayVacationUserList(targetDateString):
    pageNumber = 1
    needNextPage = True

    userStringList = []
    total = 0 
    month = ""
    day = ""

    while needNextPage:
        # print(userStringList)
        subResult = getVacationList(targetDateString, pageNumber)

        if subResult["result"] == True:
            userStringList.extend(subResult["userStringList"])
            total = subResult["Total"]
            month = subResult["month"]
            day = subResult["day"]
            
            pageNumber += 1
        else:
            needNextPage = False

    return (total, month, day, userStringList)






# 특정 날짜의 특정 페이지의 값을 가져온다. 
# 사전형식으로 result에 결과값, Total에 사용자 수, month에 달, day에 날짜 userStringList에 사용자 리스트가 들어있다. 
def getVacationList(targetDateString, page):
    params = {"pDate": targetDateString, "pPage": page}
    r = requests.post(
        url=VacationDetailURL,
        headers=requestHeader,
        data = params
    )
    data = json.loads(r.text)

    userStringList = []

    result = {
        "result":False,
        "Total":0,
        "month":"",
        "day":""
    }
    # print(data)
    if "resultCode" in data:
        if data.get("resultCode") != "SUCCESS":
            return result
        resultTable = data.get("result")
        totalCount = data.get("totalCount")
        month = data.get("month")
        day = data.get("day")
        soup = BeautifulSoup(resultTable, 'html.parser')
        if int(totalCount) < 1:
            return result
        result["month"] = month
        result["day"] = day
        result["result"] = True
        result["Total"] = totalCount
        

        userList = soup.find_all('tr')
        try: 
            for tags in userList:


                ud = tags.find_all('td')
                # <td class="C" colspan="4">휴가 신청자가 없습니다.</td>
                # ud 0 1,2,3 -> 이름 소속 종류 상태
                # 김한수 개발팀 연차(종일) 결재완료
                # 0 김한수 1 개발팀 2 연차(일차) 3 결제중

                halfdayString = ""

                type = ud[2].text
                if type != None and len(type) > 2:
                    qsi = type.find('(')
                    qei = type.find(')')
                    if qsi > 0 and qei > 0:
                        halfdayString = type[qsi+1:qei]

                if halfdayString == "종일":
                    s = "{0} {1} : {2}".format(ud[1].text,ud[0].text, ud[3].text)
                else:

                    s = "{0} {1}({2}) : {3}".format(ud[1].text,ud[0].text,halfdayString, ud[3].text)
                
                
                userStringList.append(s)
                # print(s)
        except:
            result["result"] = False
            result["Total"] = 0

            return result

        result["userStringList"] = userStringList

    return result
            

    # t = date.today()
    # # 다음달로 넘어가야 하네.
    # if t.day > day:



    # print(date.today())

holyday = set()

# 모든 주말이 아닌 휴일을 holyday 전역 변수에 담는다. 
def getHolydayList():
    conn = sqlite3.connect(dbFile)
    # Connection 으로부터 Cursor 생성
    cur = conn.cursor()
 
    # SQL 쿼리 실행
    cur.execute("select strDate from holyday")
 
    # 데이타 Fetch
    rows = cur.fetchall()
    for row in rows:
        holyday.add(row[0])
 
    # Connection 닫기
    conn.close()


# 전달받은 날짜가 일하는 날인지 판단한다.
# 전달 받은 객채가 date객채가 아니면 항상 False를 반환한다. 
def getWorkingDay(d):
    if type(d) is not date:
        return False

    if d.weekday() == 5 or d.weekday() == 6:
        return False

    tempDateString = d.strftime("%Y.%m.%d")
    if tempDateString in holyday:
        return False

    return True


# 오늘 이 일하는 날이라면.. 
# 다음 일하는 날을 골라서 휴가자를 확인하여 전달한다. 
def sendVacationUser():
    #휴일을 일단 불러온다.
    getHolydayList()

    oneDay = timedelta(days=1)

    t = date.today()

    targetDateString = ""

    # 오늘이 일하는 날이라면... 
    if getWorkingDay(t):
        #메세지를 보내야 한다. 
        #다음 일하는 날짜를 찾는다. 
        while targetDateString == "":
            # 하루 추가.
            t = t + oneDay
            #일하는 날짜라면..
            if getWorkingDay(t):
                #목표날짜로 지정. 
                targetDateString = t.strftime("%Y.%m.%d")

        print("휴가자 검사중... 검사날짜 : {0}".format(targetDateString))
        #while 문이 끝났다면 목표날짜를 찾음... 
        #목표 날짜의 휴가자를 모두 구함. 
        (total, month, day, userStringList) = getTargetDayVacationUserList(targetDateString)
        # 휴가자가 있다면..
        if int(total) > 0:
            # 텔레그램으로 전달할 메세지를 작성하기 시작한다. 
            resultString = "{0} {1} 총 휴가자 {2}명 내역입니다. \n\n".format(month,day,total)
            # 가나다 순으로 정렬하자 ... 개발팀이 가장 먼저 온다. 
            userStringList.sort()
            # 각각을 개행으로 구분하여 써준다. 
            for oneUser in userStringList:
                resultString += oneUser + "\n"
            # 텔레그램으로 전달.
            telegramModule.sendMessage(notiGroupTelegramId, resultString)
            print("휴가자 전달\n전달 텔레그램 번호 : {0}\n{1}".format(notiGroupTelegramId,resultString))

        print("휴가자 검사끝... 검사날짜 : {0}".format(targetDateString))

sendVacationUser()
