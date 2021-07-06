from bs4 import BeautifulSoup
import requests
import sys
import json
import os
import re
import time

hostURL = 'https://office.hiworks.com'

boardListURL = f"{hostURL}/{os.environ.get('MIDDLE_URL_FOR_HIWORKS_NOTI')}/bbs/board_ajax/getBoardContentsList"
boardURLForm = f"{hostURL}/{os.environ.get('MIDDLE_URL_FOR_HIWORKS_NOTI')}/bbs/board/board_view/"
contactsURL = f"{hostURL}/{os.environ.get('MIDDLE_URL_FOR_HIWORKS_NOTI')}/insa/org_ajax/"



requestHeader = ""


# 하이웍스에서 새글 리스트를 받아와서 저장된 값보다 큰것이 있는지 확인한다.
def getNewList( storedId):
    
    r = requests.get(
        url=boardListURL,
        headers=requestHeader
    )

    result = {"result":True}

    # 읽어오는것이 잘 되지 않음... 인터넷문제라던지.. 로그인 문제와 같은것들임.
    if len(r.text) < 5000:
        result["result"] = False
        result["message"] = " 읽어오는것 실패 "
        result["rsponseText"] = r.text
        return result    

    resultArticleList = []

    # 일단 값을 읽어 왔다면...
    data = json.loads(r.text)
    if "resultCode" in data:
        if data.get("resultCode") != "SUCCESS":
            result["result"] = False
            result["message"] = "json파싱하여 결과가 성공 아님. 결과:{1}".format(data.get("resultCode"))
            return result

        # 값을 잘 읽어와서 json도 정상이다. 
        articleList = data.get("result").get("LIST")

        # 글중에 가장 높은 글을 검사한다.
        newHightestID = 0

        # 각 리스트 별로 확인을 한다. 
        for oneArticle in articleList:
            # 글번호
            ano = oneArticle.get("no")
            # 게시판 번호.
            bno = oneArticle.get("fk_board_info_no")
            # 글번호와 게시판 번호로 링크를 생성한다.
            articleURL = f"{boardURLForm}/{bno}/{ano}/"

            # 현재 글중에서 가장 높은 아이디를 계산한다. 
            if newHightestID < int(ano):
                newHightestID = int(ano)

            # 저장된 아이디보다 높은 값이라면 읽어서 값을 전달 해야 한다. 
            if storedId < int(ano):
                articleData = getOneArticle(articleURL,ano)
                articleData["board_name"] = oneArticle.get("board_name")
                articleData["title"] = oneArticle.get("title")
                articleData["author"] = oneArticle.get("name")
                articleData["url"] = articleURL
                articleData["articleId"] = ano
    
                resultArticleList.append(articleData)

        result["articleList"] = resultArticleList
        result["newHightestID"] = newHightestID

    return result




def getOneArticle(articleURL, articleNo):

    result = {}

    # 파일을 다운받을 위치를 지정해 줘야 한다. 
    exefilePath = os.path.dirname(sys.argv[0])
    # 글 하나를 가져온다.
    ar = requests.get(
        url=articleURL,
        headers=requestHeader
    )
    soup = BeautifulSoup(ar.text, 'html.parser')
    # 컨텐츠 부분을 잘라냄.
    content_raw = soup.find('div',{'class':'boardview'})

    content_without_poll=[]

    # 컨텐츠 부분중에서 투표 부분을 제외하고 모든 태그를 한곳에 모음.
    for tags in content_raw.children:
        if tags.name != None:
            if ('id' in tags.attrs and tags['id'] == 'pull_div') == False:
                content_without_poll.append(tags)

    content_only_p_tag = []
    # 모은 태그 중에서 p 태그만 따로 모음.
    for lines in content_without_poll:
        # 스스로 p태그라면 본인 저장. 
        if lines.name == 'p':
            content_only_p_tag.append(lines)
        else:
            # p태그가 아니면 하위 돌면서 p만 찾아서 저장.
            p_list = lines.find_all('p')
            for ps in p_list:
                content_only_p_tag.append(ps)

    # 모든 p 태그를 모아서 글로 만듬. 
    content = "\n".join(x.text for x in content_only_p_tag )

    result["content"] = content
    result["fileExist"] = False

    # 파일 부분을 잘라냄.
    files_raw = soup.find_all('div',{'class':'addFiles'})
    
    files = None
    # 파일이 있다면. 
    if len(files_raw) > 0:
        result["fileExist"] = True

        # 파일을 담을 폴더를 생성하고.
        fileFolder = "{0}/{1}".format(exefilePath,articleNo)
        if os.path.exists(fileFolder) == False:
            os.mkdir(fileFolder)

        result["fileFolder"] = fileFolder

        files_list_raw = files_raw[0].find_all('a')
        files_list = []
        for x in files_list_raw:
            # 링크중에 이름과 링크가 있는 녀석만.
            if x['href'] != '#' and x.text != "":
                files_list.append(x)

                filePath = "{0}/{1}".format(fileFolder,x.text)
                # 파일을 모두 다운 받자.
                downlaodAFile(filePath, hostURL+x['href'])

        files = "\n".join(x.text for x in files_list )
        result["files"] = files
                
    return result


def downlaodAFile(filePath, fileUrl):
    with open(filePath, "wb") as file: 
        fileDownload = requests.get(
            url=fileUrl,
            headers=requestHeader  
        )
        file.write(fileDownload.content)


def deleteSentFiles(fileFolder):
    filelist = os.listdir(fileFolder)
    for filename in filelist:
        filePath = "{0}/{1}".format(fileFolder,filename)
        if os.path.isfile(filePath):
            os.remove(filePath)
    os.rmdir(fileFolder)


def getAContact(pUserNo):
    # 개인 주소록 정보를 하나 가져온다. 

    ac = requests.post(
        url=contactsURL,
        headers=requestHeader,
        data={'pMenu':'org_member_info','pUserNo':pUserNo}
    )

    result = {"result":False}

    data = json.loads(ac.text)
    if "resultCode" in data:
        if data.get("resultCode") != "SUCCESS":
            result["message"] = f"json 파싱하여 결과가 성공 아님. 결과:{data['resultCode']}"
            result["rawData"] = ac.text
            return result

        result["result"] = True
        soup = BeautifulSoup(data.get("result"), 'html.parser')

        profile = soup.find('div', {'class':'profile'})
        profile_img = profile.find('img')

        profile_img_src = hostURL + profile_img['src']


        # 이름과 직책
        contact_raw_name = soup.find('div',{'class':'proflie_right'})
        # 연락처 
        contact_raw_number = soup.find('dl',{'class':'gon'})

        contact_raw_name_list = contact_raw_name.find_all('dd')
        name_size = len(contact_raw_name_list)

        personData = {}



        for i in range(name_size):
            # 처음은 이름 마지막은 직책이다. 
            if i == 0:
                personData["name"] = contact_raw_name_list[i].text
            elif i == name_size - 1:
                personData["position"] = contact_raw_name_list[i].text.strip() 
            else:
                personData[f"name_etc_{i}"] = contact_raw_name_list[i].text.strip()

        # 이름을 찾았으니 사진 url을 저장한다. 
        profile = soup.find('div', {'class':'profile'})
        profile_img = profile.find('img')

        profile_img_src = hostURL + profile_img['src']
        personData["profile_img_src"] = profile_img_src
        # exefilePath = os.path.dirname(sys.argv[0])
        # filePath = f"{exefilePath}/{personData['name']}.jpg"
        # downlaodAFile(filePath, profile_img_src)
        # personData["profile_img_src"] = profile_img_src


        contact_raw_number_title_list = contact_raw_number.find_all('dt')
        contact_raw_number_detail_list = contact_raw_number.find_all('dd')
        
        # 그외 연락처
        number_size = len(contact_raw_number_title_list)
        for i in range(number_size):
            # print(contact_raw_number_title_list[i].text)
            # print(contact_raw_number_detail_list[i].text)
            personData[contact_raw_number_title_list[i].text.strip()] = contact_raw_number_detail_list[i].text.strip()

        result["personData"] = personData


    return result



