import requests
import sys
import os
import imghdr
import mimetypes
import telebot
from PIL import Image



botToken = os.environ.get("TELEGRAM_BOT_TOKEN_FOR_HIWORKS_NOTI")

bot = telebot.TeleBot(botToken)

# 텔레그램으로 메세지를 전달해주는 함수
# 대화방 아이디와 메세지를 받아서 전달해준다.
def sendMessage(chatid, text):
    r = bot.send_message(chatid,text,parse_mode="html")

# 텔레그램으로 파일을 전송한다. 
# tempFilename은 텔레그램으로 파일 전송시 유니코드 파일명은 오류가 발생하여 임시파일명으로 전달항 경우 전달 해주면 된다. 
# 전달이 안될경우 진짜 파일명으로 전송한다. 
def sendFile(chatid, filePath):
    
    if os.path.exists(filePath) is False or  os.path.isfile(filePath) is False:
        return 

    inputFileContent = open(filePath,'rb').read()
    filename = getFilenameFromPath(filePath)

    # mimetype 을 결정해보자.
    # 먼저 이미지검사..
    image = imghdr.what(None, inputFileContent)
    #이미지라면.
    if image:
        bot.send_photo(chatid, open(filePath,'rb'), caption=filename)
    else:
        bot.send_document(chatid, open(filePath,'rb'))

def getFilenameFromPath(filePath):
    position = filePath.rfind('/')
    if position>0:
        return filePath[position+1:]
    return filePath

