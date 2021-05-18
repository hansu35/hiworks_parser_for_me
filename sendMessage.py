import telegramModule
import os


adminId = os.environ.get("TELEGRAM_ID_OF_ADMIN_FOR_HIWORKS_NOTI")
sendMessage(adminId, "테스트 메세지 전송.")