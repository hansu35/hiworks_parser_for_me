from bs4 import BeautifulSoup
import requests
import sys
import json
import os
import re
import time


# 신규 api 로 변경된 하이웍스 처리 함수 

# 휴가 관련
#휴가 전체 url 
vacationUrl = 'https://hr-work-api.office.hiworks.com/v4/vacation-calendar?filter%5Byear%5D={0}&filter%5Bmonth%5D={1}&page%5Blimit%5D=600&page%5Boffset%5D=0'
#사용자 정보 
userDataUrl = 'https://office-account-api.office.hiworks.com/v3/users?filter%5Bwith_inactivated%5D=Y&filter%5Bwith_deleted%5D=Y&fields%5Busers%5D=name'

# 세션 아이디를 가져 오자. 
sessionid = os.environ.get("SESSION_ID_FOR_HIWORKS_NOTI")

requestHeader = {"Cookie": "PHPSESSID={0};".format(sessionid),
             "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"
             }



# 사용자 정보 일부 가져온다. id와 이름. 
# 부서 정보는 부서정보(부서아이디, 명칭), 멤버정보(사용자아이디, 부서아이디)를 모두 가져와야 한다. 귀찮..
def getUserData():
    r = requests.get(
        url=userDataUrl,
        headers=requestHeader
    )

    userDict = {}

    # 읽어오는것이 잘 되지 않음... 인터넷문제라던지.. 로그인 문제와 같은것들임.
    if len(r.text) < 5000:
        return userDict

    # json 파싱을 시작.
    data = json.loads(r.text)

    userList = data.get("data")

    
    for user in userList:

        userID = int(user.get("id"))
        userName = user.get("attributes").get("name")
        userDict[userID] = userName

        

    return userDict



# 휴가 정보 사용자 아이디와 휴가 날짜 가져온다. 
# 휴가 사용자의 정보를 반환한다. 
# 사용자 정보는 이름, 결제여부, 시간, 시작시간, 종료시간 
def getVacationData(targetDate, year, month, userData):
    r = requests.get(
        url=vacationUrl.format(year,month),
        headers=requestHeader
    )

    result = {
        "result":False,
        "total":0
    }
    totalCount = 0

    vacationUserList = []

    # 읽어오는것이 잘 되지 않음... 인터넷문제라던지.. 로그인 문제와 같은것들임.
    if len(r.text) < 5000:
        return result

    # json 파싱을 시작.
    data = json.loads(r.text)

    vacationDataList = data.get("data")
    for vac in vacationDataList:
        
        # 목표하는 날짜의 휴가라면 표시해준다. 
        if vac.get("date") == targetDate:

            name = userData[vac.get("office_user_no")]
            # 하루 휴가 인지 시간 휴가인지 구분필요.
            if vac.get("type") != "days":
                # 연차가 아닌경우 어떻게 하지? 
                # print(f"{vac.get("hours")} {vac.get("start_time")} {vac.get("end_time")}")
                print("{0},{1},{2}".format(vac.get("hours"), vac.get("start_time"), vac.get("end_time")))

            vacationUserList.append( (name, vac.get("approval_status"), vac.get("hours"), vac.get("start_time"), vac.get("end_time")) )
            totalCount+=1

    result['result'] = True
    result['total'] = totalCount
    result["vacationUserList"] = vacationUserList

    return result









