import hiworks
import telegramModule
import os
import sys
import time


adminTelegramId = os.environ.get("TELEGRAM_ID_OF_ADMIN_FOR_HIWORKS_NOTI")
notiGroupTelegramId = os.environ.get("TELEGRAM_GROUP_ID_OF_ADMIN_FOR_HIWORKS_NOTI")
# notiGroupTelegramId = os.environ.get("TELEGRAM_ID_OF_ADMIN_FOR_HIWORKS_NOTI")

# 환경설정 파일 읽기.
exefilePath = os.path.dirname(sys.argv[0])
# exefilePath = os.path.dirname(os.path.realpath(__file__))
idFilePath = exefilePath+'/tempLast.id'

# 로그 남기는 함수.
def notiLog(message):
    todayString = time.strftime('%Y_%m_%d', time.localtime(time.time()))
    nowTimeString = time.strftime('[%Y %m %d %H:%M:%S %a]', time.localtime(time.time()))
    
    # logfilePath = exefilePath+'/check.checklog'

    # with open(logfilePath, 'a') as fp:
    #     fp.write(nowTimeString + message+"\n")
    print(message)

def htmlStrip(text):
	return text.replace("<","&lt;").replace(">","&gt;").replace("&","&amp;")

#메세지를 보내는 함수 적당한 문자열을 만들어서 메러모스트와 텔레그램으로 게시판 글을 전달 해준다.
def sendMessage(articleData):
# def sendMessage(boardName, title, url, author, content, files):
    #텔레그램은 문자열을 만들어 준다.
    text = "{0}\n<a href='{1}'>{2} - 작성자:{3}</a>\n\n{4}\n\n".format(
        articleData["board_name"], 
        articleData["url"], 
        htmlStrip(articleData["title"]), 
        articleData["author"], 
        htmlStrip(articleData["content"]))
    
    if articleData["fileExist"]:
        text = text + "<b>첨부파일</b>\n" + articleData["files"]
    
    notiLog("{0} 에게 {1} 제목의 글을 보냄".format(notiGroupTelegramId, articleData["title"]))
    telegramModule.sendMessage(notiGroupTelegramId, text)

    fileIndex = 1

    # 파일도 보내볼까? 
    if articleData["fileExist"]:
        fileFolder = articleData["fileFolder"]
        filelist = os.listdir(fileFolder)
        for filename in filelist:
            notiLog("sending...||{0}/{1}".format(fileFolder,filename))
            fileExt = os.path.splitext(filename)[1]
            fileSendingResult = telegramModule.sendFile(
                notiGroupTelegramId, 
                "{0}/{1}".format(fileFolder,filename)
                )
        


# 아이디 파일이 없으면 0으로 세팅한다. 나오는 모든 글을 검사해서 전달하게 된다.
if os.path.isfile(idFilePath) is False:
    fp = open(idFilePath, 'w')
    fp.write("0")
    fp.close()


# 세션 아이디를 가지고 오자. 
sessionid = os.environ.get("SESSION_ID_FOR_HIWORKS_NOTI")


# 마지막으로 읽은 파일 게시글의 숫자를 가지고 온다.
fp = open(idFilePath, 'r')
line = fp.readline()
fp.close()
notiLog("=================검사시작=================")
notiLog("파일에 저장되어 있던 마지막 점검 글의 아이디"+line)
storedlastid = int(line)
newLastId = 0


# 로그인 해더를 추가한다.
hiworks.requestHeader = {"Cookie": "PHPSESSID={0};".format(sessionid),
             "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"
             }


result = hiworks.getNewList(storedlastid)
if result["result"] == False:
    telegramModule.sendMessage(adminTelegramId,"하이웍스 파싱에 오류가 발생하였습니다. "+result["message"])
    notiLog("하이웍스 파싱에 오류가 발생함.")
    notiLog(result["rsponseText"])
    exit()

articleList = result["articleList"]
for oneArticle in articleList:
    sendMessage(oneArticle)

newLastId = result["newHightestID"]
notiLog("검사후 가장 최신의 글 번호 {0}".format(newLastId))

if newLastId > storedlastid:
    fp = open(idFilePath,'w')
    fp.write(str(newLastId))
    fp.close()
    notiLog("검사후 기존 저장 번호 {0}, 신규 저장번호 {1}".format(storedlastid, newLastId))

notiLog("!!!!!!!!!!!!!!    검사끝    !!!!!!!!!!!!!!!!")
#echo '::set-output name=SELECTED_COLOR::green'
print("::set-output name=list_count::"+ str(newLastId - storedlastid) + "")








