import telegramModule
import os
import sys
import time
from datetime import date
from datetime import timedelta
import hiworksNewAPI

# 텔래그램 아이디를 가지고 오자.
notiGroupTelegramId = os.environ.get("TELEGRAM_GROUP_ID_OF_ADMIN_FOR_HIWORKS_NOTI")
# notiGroupTelegramId = os.environ.get("TELEGRAM_ID_OF_ADMIN_FOR_HIWORKS_NOTI")

exefilePath = os.path.dirname(sys.argv[0])

#검사해야 하는 이름 
user1Name = os.environ.get("USER_1_NAME_FOR_HIWORKS_NOTI")
user2Name = os.environ.get("USER_2_NAME_FOR_HIWORKS_NOTI")


# 전달받은 날짜가 일하는 날인지 판단한다.
# 전달 받은 객채가 date객채가 아니면 항상 False를 반환한다. 
def getWorkingDay(d):
    if type(d) is not date:
        return False

    if d.weekday() == 5 or d.weekday() == 6:
        return False

    return True


def sendVaction():
    #오늘 날짜
    t = date.today()

    oneDay = timedelta(days=1)

    targetDateString = ""
    targetMonthString = ""
    targetYearString = ""

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
                targetDateString = t.strftime("%Y-%m-%d")
                targetMonthString = t.strftime("%m")
                targetYearString = t.strftime("%Y")


        print("휴가자 검사중... 검사날짜 : {0}".format(targetDateString))
        #while 문이 끝났다면 목표날짜를 찾음... 
        #목표 날짜의 휴가자를 모두 구함. 

        userNameData = hiworksNewAPI.getUserData()

        if len(userNameData)<1:
            print("로그인 오류인것으로 보임. ")
            return False


        vacationData = hiworksNewAPI.getVacationData(targetDateString, targetYearString, targetMonthString, userNameData)
        # vacationUserList.sort()
        vacationUserList = vacationData['vacationUserList']
        total = vacationData['total']
        print(vacationUserList)

        messageString = f"{targetDateString} 휴가자 총 {total}명 입니다. \n"
        if total > 0:
            vacationUserList.sort()

            for (name, approvalStatus, hours, startTime, endTime ) in vacationUserList:
                if hours == 0:
                    messageString += f"\n{name} : {approvalStatus}"
                else:
                    messageString += f"\n{name} : {approvalStatus} / {hours}시간 ({startTime}-{endTime})"

                if user1Name == name:
                    newFileWrites = True
                    vacFilePath = exefilePath+"/user1.vac"
                    with open(vacFilePath, 'w') as fp:
                        fp.write(targetDateString)

                if user2Name == name:
                    newFileWrites = True
                    vacFilePath = exefilePath+"/user2.vac"
                    with open(vacFilePath, 'w') as fp:
                        fp.write(targetDateString)

            # 텔레그램으로 전달.
            telegramModule.sendMessage(notiGroupTelegramId, messageString)

        # print(messageString)

        print("휴가자 검사끝... 검사날짜 : {0}".format(targetDateString))

    return newFileWrites



newFileWrites = sendVaction()
print(f"::set-output name=new_file::{newFileWrites}")








