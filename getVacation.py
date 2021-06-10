import telegramModule
import os
import sys
import time
from datetime import date
from datetime import timedelta
import sqlite3

import hiworksVacation


# 환경설정 파일 읽기.
exefilePath = os.path.dirname(sys.argv[0])
dbFile = exefilePath+'/holyday.db'

# 텔래그램 아이디를 가지고 오자.
# notiGroupTelegramId = os.environ.get("TELEGRAM_GROUP_ID_OF_ADMIN_FOR_HIWORKS_NOTI")
notiGroupTelegramId = os.environ.get("TELEGRAM_ID_OF_ADMIN_FOR_HIWORKS_NOTI")


#검사해야 하는 이름 
user1Name = os.environ.get("USER_1_NAME_FOR_HIWORKS_NOTI")

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

    newFileWrites = False

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
        (total, month, day, userList) = hiworksVacation.getTargetDayVacationUserList(targetDateString)

        # 휴가자가 있다면..
        if int(total) > 0:
            # 텔레그램으로 전달할 메세지를 작성하기 시작한다. 
            resultString = "{0} {1} 총 휴가자 {2}명 내역입니다. \n\n".format(month,day,total)
            # 가나다 순으로 정렬하자 ... 개발팀이 가장 먼저 온다. 
            userList.sort()
            # 각각을 개행으로 구분하여 써준다. 
            for team, name, duration, approvalStatus in userList:
                if duration != "종일":
                    resultString += f"{team} {name}({duration}) : {approvalStatus}\n"
                else:
                    resultString += f"{team} {name} : {approvalStatus}\n"

                if user1Name == name: 
                    if duration == "종일" or duration == "오전":
                        newFileWrites = True
                        vacFilePath = exefilePath+"/user1.vac"
                        with open(vacFilePath, 'w') as fp:
                            fp.write(targetDateString+"\n")



            # 텔레그램으로 전달.
            telegramModule.sendMessage(notiGroupTelegramId, resultString)
            print("휴가자 전달\n전달 텔레그램 번호 : {0}\n{1}".format(notiGroupTelegramId,resultString))

        print("휴가자 검사끝... 검사날짜 : {0}".format(targetDateString))

    return newFileWrites

newFileWrites = sendVacationUser()
print(f"::set-output name=new_file::{newFileWrites}")
