import json
import os
from bs4 import BeautifulSoup
import requests



"""
하이웍스에서 지정한 날짜의 휴가자를 모두 가져오는 것을 담당하는 모듈을 만든다.
"""

# 휴가자를 얻을수 있는 URL
VacationDetailURL = os.environ.get("VACATION_URL_FOR_HIWORKS_NOTI")

# 세션 아이디를 가지고 오자. 
sessionid = os.environ.get("SESSION_ID_FOR_HIWORKS_NOTI")


#리퀘스트 해더.
requestHeader = {"Cookie": "PHPSESSID={0};".format(sessionid),
             "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
             "Content-Type": "application/x-www-form-urlencoded"
             }


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
                # 홍길동 개발팀 연차(종일) 결재완료
                # 0 홍길동 1 개발팀 2 연차(일차) 3 결제중

                halfdayString = ""

                type = ud[2].text
                if type != None and len(type) > 2:
                    qsi = type.find('(')
                    qei = type.find(')')
                    if qsi > 0 and qei > 0:
                        halfdayString = type[qsi+1:qei]

                # userStringList.append(s)
                # 듀블로 구조체 말고 저장을 해서 넘기자. 
                userStringList.append( (ud[1].text,ud[0].text,halfdayString, ud[3].text) )
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