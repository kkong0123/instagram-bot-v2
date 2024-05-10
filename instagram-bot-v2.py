import json
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from PyQt5.QtCore import *
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
import sys, os, time, random
import logging
import logging.handlers
import requests
import resource

logger = logging.getLogger(__name__)
formatter = logging.Formatter('[%(levelname)s | %(filename)s : %(lineno)s] %(asctime)s > %(message)s')
fileHandler = logging.handlers.RotatingFileHandler(filename='./log/traceback.log', maxBytes = 10*1024*1024, backupCount = 5)
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("",exc_info=(exc_type, exc_value, exc_traceback))
    sys.exit(0)

sys.excepthook = handle_exception

#Global Variables
global textBrowser_msglog
global actionNum

# global driver

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

form = resource_path('worker_kr.ui')
form_class = uic.loadUiType(form)[0]

#Worker Class

class Worker(QThread):

    def __init__(self, parent):
        super().__init__(parent)
        self.power = True
        self.parent = parent
        
    def run(self): # This is an Action Groupbox Activate/Deactivate Function
        # Get Action Index
        while self.power:
            if actionNum == 1:
                # Action Bot

                self.parent.pushButton_activate.setEnabled(False)
                self.parent.pushButton_deactivate.setEnabled(True)
                self.parent.login()

                for tag in range(self.parent.listWidget_tag.count()):
                    hash_tag = self.parent.listWidget_tag.item(tag).text()
                    try:
                        self.parent.search(hash_tag)
                    except Exception as e:
                        try:
                            logErr(str(e))
                            logMsg("{0} 태그 ㅣ 다시 접근을 시도합니다.")
                            self.parent.search(hash_tag)
                        except Exception as e:
                            logErr(str(e))
                            logMsg("로딩 오류 반복, 네트워크 안정성을 확보해주세요. 다음 태그로 넘어갑니다.")
                            continue
                    self.parent.bot(int(self.parent.lineEdit_repetition.text()))

                logMsg("모든 작업이 완료 되었습니다.")
                self.stop()

            if actionNum == 2:
                # Action Unfollow

                self.parent.pushButton_activate.setEnabled(False)
                self.parent.pushButton_deactivate.setEnabled(True)
                self.parent.login()
                self.parent.unfollow()

                logMsg("모든 작업이 완료 되었습니다.")
                self.stop()
                
            if actionNum == 3:
                # Action Management

                self.parent.pushButton_activate.setEnabled(False)
                self.parent.pushButton_deactivate.setEnabled(True)
                self.parent.login()
                self.parent.Management()

                logMsg("모든 작업이 완료 되었습니다.")
                self.stop()
        
            if actionNum == 4:
                # Action LoaderFunc

                self.parent.login()
                self.parent.loaderFunction()

                logMsg("모든 작업이 완료 되었습니다.")
                self.stop()                

    def stop(self):
        self.power = False
        self.parent.pushButton_activate.setEnabled(True)
        self.parent.pushButton_deactivate.setEnabled(False)
        logMsg("작업 종료")
        driver.quit()
        self.quit()
        self.wait(2000)

#WindowClass Class

class WindowClass(QMainWindow, form_class) :

    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        
        self.pushButton_activate.clicked.connect(self.WorkerStart)
        self.pushButton_deactivate.clicked.connect(self.WorkerStop)
        self.pushButton_substract.clicked.connect(self.WorkerStartLoader)

        self.pushButton_tagadd.clicked.connect(self.pushButtonTagAdd)
        self.pushButton_commentadd.clicked.connect(self.pushButtonCommentAdd)
        self.pushButton_commentadd_2.clicked.connect(self.pushButtonCommentAdd_2)
        # self.pushButton_spamuseradd.clicked.connect(self.pushButtonSpamuserAdd)

        self.pushButton_tagdel.clicked.connect(self.pushButtonTagDel)
        self.pushButton_commentdel.clicked.connect(self.pushButtonCommentDel)
        self.pushButton_commentdel_2.clicked.connect(self.pushButtonCommentDel_2)
        # self.pushButton_spamuserdel.clicked.connect(self.pushButtonSpamuserDel)

        self.checkBox_comment.stateChanged.connect(self.buttonStat)

        self.pushButton_LoadList.clicked.connect(self.pushButtonLoadList)

        self.comboBox_action.currentIndexChanged.connect(self.comboBoxActionFunc)
        self.comboBox_sup.currentIndexChanged.connect(self.comboBoxSupFunc)

        self.pushButton_LoadList.clicked.connect(self.pushButtonLoadListFunc)
        self.pushButton_Save.clicked.connect(self.pushButtonSave)
        self.pushButton_Load.clicked.connect(self.pushButtonLoad)

        #Global Variables
        global textBrowser_msglog
        textBrowser_msglog = self.textBrowser_msglog

    #QT Objects Function

    def pushButtonLoadListFunc(self):
        self.pushButton_LoadList.setEnabled(False)

    def comboBoxActionFunc(self):
        if(self.comboBox_action.currentIndex() == 0) :
            self.stackedWidget.setCurrentIndex(0)
            self.lineEdit_repetition.setEnabled(True)
            self.groupBox_Function.setEnabled(True)
        else :
            self.stackedWidget.setCurrentIndex(1)
            self.comboBox_sup.setCurrentIndex(0)
            self.lineEdit_repetition.setEnabled(False)
            self.groupBox_Function.setEnabled(False)
    
    def comboBoxSupFunc(self):
        if self.comboBox_sup.currentIndex() == 0:
            self.radioButton.setText("언팔로워")
            self.radioButton_2.setText("팔로잉")
            self.groupBox_Function.setEnabled(False)
        else:
            self.radioButton.setText("팔로워")
            self.radioButton_2.setText("팔로잉")
            self.groupBox_Function.setEnabled(True)

    def pushButtonTagAdd(self):
        if self.lineEdit_tag.text():
            self.listWidget_tag.addItem(self.lineEdit_tag.text())
            self.lineEdit_tag.clear()
    def pushButtonTagDel(self):
        self.listWidget_tag.takeItem(self.listWidget_tag.currentRow())
    def pushButtonCommentAdd(self):
        if self.lineEdit_comment.text():
            self.listWidget_comment.addItem(self.lineEdit_comment.text())
            self.lineEdit_comment.clear()
    def pushButtonCommentAdd_2(self):
        if self.lineEdit_comment_2.text():
            self.listWidget_comment_2.addItem(self.lineEdit_comment_2.text())
            self.lineEdit_comment_2.clear()
    def pushButtonCommentDel(self):
        self.listWidget_comment.takeItem(self.listWidget_comment.currentRow())
    def pushButtonCommentDel_2(self):
        self.listWidget_comment_2.takeItem(self.listWidget_comment_2.currentRow())    
    
    def pushButtonLoadList(self):
        f = open("./accountList/Follower.txt", 'r') 
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            self.listWidget_followers.addItem(line)
        f.close()

        f = open("./accountList/Following.txt", 'r') 
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            self.listWidget_following.addItem(line)
        f.close()
        
        f = open("./accountList/Unfollowers.txt", 'r') 
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            self.listWidget_unfollowers.addItem(line)
        f.close()

    def pushButtonSave(self):
        QMessageBox.information(self, "QMessageBox", "설정이 저장되었습니다.")
        logMsg("설정이 저장되었습니다.")
        
        with open("./data.json", encoding='utf-8') as f:
            data = json.load(f)     
        tag_list = []
        comment_list = []

        for x in range(self.listWidget_tag.count()):
            tag_list.append(self.listWidget_tag.item(x).text())
        data["tag"] = tag_list
        
        for x in range(self.listWidget_comment.count()):
            comment_list.append(self.listWidget_comment.item(x).text())
        data["comment"] = comment_list  

        data["repetition"] = self.lineEdit_repetition.text()
        data["delay"] = self.lineEdit_delay.text()

        with open("./data.json", 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, indent=4)

    # 데이터 저장/불러오기
    def pushButtonLoad(self): 
        QMessageBox.information(self, "QMessageBox", "불러오기가 완료되었습니다.")
        logMsg("불러오기가 완료되었습니다.")

        self.listWidget_tag.clear()
        self.listWidget_comment.clear()
        self.lineEdit_repetition.clear()
        self.lineEdit_delay.clear()

        with open("./data.json", encoding='utf-8') as f:
            data = json.load(f)  

        for tag in data["tag"]:
            self.listWidget_tag.addItem(tag)
        for comment in data["comment"]:
            self.listWidget_comment.addItem(comment)
        self.lineEdit_repetition.setText(data["repetition"])
        self.lineEdit_delay.setText(data["delay"])

    # 쓰레드 시작 함수
    def WorkerStart(self):
        global actionNum
        actionNum = int(self.comboBox_action.currentIndex()) + 1
        if actionNum == 2:
            if self.comboBox_sup.currentIndex() == 0:
                actionNum = 2
            else:
                actionNum = 3

        self.worker = Worker(self)
        self.worker.start()

    def WorkerStartLoader(self):
        global actionNum
        actionNum = 4
        self.worker = Worker(self)
        self.worker.start()        
    
    def WorkerStop(self):
        self.worker.stop()

    # 봇 함수
    def bot(self, repeat_cnt):
        global i_cnt
        for i_cnt in range(int(repeat_cnt)):
            if self.checkBox_avoidFunc.isChecked():
                if (i_cnt+1) % 15 == 0:
                    driver.find_element_by_css_selector("._aaqg ._abl-").click() # Next
                    logMsg("매크로 감지 우회 기능 사용 중.. {0}번째 작업 건너뛰기".format(i_cnt+1))
                    continue

            self.avoidFunction(i_cnt)

            try:
                try:
                    follow_text = driver.find_element_by_css_selector("._aar2 ._aade").text
                except Exception as e:
                    logErr(str(e))
                    follow_text = "NUll"

                if follow_text == "팔로우" or follow_text == "Follow":
                    self.checkCnt() 
                    if self.checkBox_like.isChecked():
                        self.like()

                    if self.checkBox_follow.isChecked():
                        randomNum = random.randint(1, 100)
                        percentage = int(self.comboBox_percentage.currentText())

                        if randomNum <= percentage:
                            self.follow()
                        else:
                            logMsg("팔로우 기능 건너뛰기")

                    if self.checkBox_comment.isChecked():
                        self.comment()

                    if self.checkBox_like.isChecked():
                        if self.lineEdit_N.text():
                            if int(self.lineEdit_N.text()) > 1:
                                self.likeRepeat(int(self.lineEdit_N.text()))

                    driver.find_element_by_css_selector("._aaqg ._abl-").click()
                    logMsg("다음 게시물 이동 중..")

                    driver.implicitly_wait(30)
                    time.sleep(random.uniform(3,6))

                else:
                    logMsg("[이미 팔로우한 계정!]. [{0}]번째 작업 건너뛰기".format(i_cnt+1))

                    time.sleep(random.uniform(3,6))
                    driver.find_element_by_css_selector("._aaqg ._abl-").click()
                    logMsg("다음 게시물 이동 중..")

                    driver.implicitly_wait(30)
                    time.sleep(random.uniform(10,20))

            except Exception as e:
                f = open("./log/log.txt",'a')
                f.write(time.strftime('%x [%H:%M:%S] ') + "\n" + str(e) + "\n")                
                time.sleep(random.uniform(3,6))
                driver.find_element_by_css_selector("._aaqg ._abl-").click()
                logMsg("에러 발생!, 다음 게시물 이동 중..")

                driver.implicitly_wait(30)
                time.sleep(random.uniform(60,80))

    # 팔로워 팔로우 추출 함수
    def loaderFunction(self):

        logMsg("팔로워 추출 중...")
        QApplication.processEvents()   

        url = 'https://www.instagram.com/' + self.lineEdit_id.text() +'/followers'
        driver.get(url)
        driver.implicitly_wait(30)
        time.sleep(18)

        # scroll
        scroll_box = driver.find_element_by_css_selector("._aano")
        while True:
            last_ht = driver.execute_script("return arguments[0].scrollHeight;",scroll_box)
            driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);",scroll_box)
            QApplication.processEvents()
            time.sleep(random.uniform(1,11))
            ht = driver.execute_script("return arguments[0].scrollHeight;",scroll_box)
            if ht == last_ht:
                QApplication.processEvents()
                time.sleep(random.uniform(3,15))
                driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);",scroll_box)
                ht = driver.execute_script("return arguments[0].scrollHeight;",scroll_box)
                if ht == last_ht:
                    break
                else:
                    last_ht = ht
                    continue
        
        open("./accountList/Follower.txt", 'w').close()
        open("./accountList/Following.txt", 'w').close()
        open("./accountList/Unfollowers.txt", 'w').close()

        follower_list = []
        follower = driver.find_elements_by_css_selector("div > div > span > a > span")

        for fr in follower:
            fr_text = str(fr.text)
            if fr_text.find("인증됨") != -1:
                fr_text = fr_text[:fr_text.find("\n인증됨")]
            follower_list.append(fr_text)

        for t in follower_list: 
            f = open("./accountList/Follower.txt",'a')
            data = t +"\n"
            f.write(data)
        f.close()        

        logMsg("팔로워 리스트 추출 완료! 텍스트 파일을 확인하세요.")
        QApplication.processEvents()   

        
        url = 'https://www.instagram.com/' + self.lineEdit_id.text() +'/following' # 팔로잉 정보 수집 
        driver.get(url)
        driver.implicitly_wait(30)
        time.sleep(18)

        logMsg("팔로잉 추출 중...")
        QApplication.processEvents()   

        # scroll
        scroll_box = driver.find_element_by_css_selector("._aano")
        while True:
            last_ht = driver.execute_script("return arguments[0].scrollHeight;",scroll_box)
            driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);",scroll_box)
            QApplication.processEvents()
            time.sleep(random.uniform(1,11))
            ht = driver.execute_script("return arguments[0].scrollHeight;",scroll_box)
            if ht == last_ht:
                QApplication.processEvents()
                time.sleep(random.uniform(5,15))
                driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);",scroll_box)
                ht = driver.execute_script("return arguments[0].scrollHeight;",scroll_box)
                if ht == last_ht:
                    break
                else:
                    last_ht = ht
                    continue        

        following_list = []
        following = driver.find_elements_by_css_selector("div > div > span > a > span")
        for fg in following:
            fg_text = str(fg.text)
            if fg_text.find("인증됨") != -1:
                fg_text = fg_text[:fg_text.find("\n인증됨")]
            following_list.append(fg_text)

        for t in following_list:
            f = open("./accountList/Following.txt",'a')
            data = t +"\n"
            f.write(data)
        f.close()

        logMsg("팔로잉 리스트 추출 완료! 텍스트 파일을 확인하세요.")
        QApplication.processEvents()   

        logMsg("언팔로워 추출 중...")
        QApplication.processEvents()   

        following_sub_follower = [x for x in following_list if x not in follower_list]

        for t in following_sub_follower: 
            f = open("./accountList/Unfollowers.txt",'a')
            data = t +"\n"
            f.write(data)
        f.close()

        logMsg("언팔로워 리스트 추출 완료! 텍스트 파일을 확인하세요.")
        QApplication.processEvents()   

        logMsg("추출 작업이 완료 되었습니다.")
        QApplication.processEvents()    

    # 인스타그램 로그인 함수
    def login(self):

        global driver

        if getattr(sys, 'frozen', False): # 가상 메모리에 경로 만들기
            chromedriver_path = os.path.join(sys._MEIPASS, "./chromedriver")
            driver = webdriver.Chrome(chromedriver_path)
        else:
            driver = webdriver.Chrome('./chromedriver')


        url = 'https://www.instagram.com/accounts/login/'
        driver.get(url)
        driver.implicitly_wait(15)
        driver.find_element_by_css_selector("._ab32:nth-child(1) ._ac4d").send_keys(self.lineEdit_id.text())
        time.sleep(random.randint(10, 15))
        driver.find_element_by_css_selector("._ab32+ ._ab32 ._ac4d").send_keys(self.lineEdit_pw.text())
        time.sleep(random.randint(10, 15))


        id_element = driver.find_element_by_css_selector("._ab32:nth-child(1) ._ac4d")
        id_element = id_element.get_attribute('value')

        driver.find_element_by_css_selector("._acap").click()
        driver.implicitly_wait(15)


        time.sleep(random.randint(10, 15))

        if driver.current_url == 'https://www.instagram.com/accounts/onetap/?next=%2F':
            logMsg("인스타그램 로그인 성공!")
        else:
            logMsg("인스타그램 로그인 실패, 다시 시도 해주세요.")
            self.WorkerStop()

    # 해시태그 검색 함수
    def search(self, hash_tag): 
        url = 'https://www.instagram.com/explore/tags/' + hash_tag
        driver.get(url)
        driver.implicitly_wait(35)

        logMsg("해시태그 검색 중..")
        time.sleep(random.randint(10, 20))

        pic_list = driver.find_elements_by_css_selector("._aagw , ._aanf:nth-child(1) ._a6hd")
        pic_list = list(pic_list)
        driver.implicitly_wait(15)
        time.sleep(5)
        pic_list[0].click()
        driver.implicitly_wait(15)
        time.sleep(5)
        try:
            # 인기게시물 건너뛰기
            for i in range(9):
                driver.find_element_by_css_selector("._aaqg ._abl-").click()
                logMsg("{0}번째 인기 게시물 건너 뛰는 중..".format(i+1))
                driver.implicitly_wait(15)
                time.sleep(5)
        except Exception as e:
            logErr(str(e))
            logMsg("{0} 태그는 최근 게시물 접근이 불가합니다.".format(hash_tag))

    def randomMessage(self):
        if (self.comboBox_action.currentIndex() == 1) and (self.comboBox_sup.currentIndex() == 1):
            return self.listWidget_comment_2.item(random.randint(0, self.listWidget_comment_2.count() - 1)).text()
        else:
            return self.listWidget_comment.item(random.randint(0, self.listWidget_comment.count() - 1)).text()

    # 체크 개수 구하기 함수
    def checkCnt(self):
        count = 0
        if self.checkBox_like.isChecked():
            count += 1
        if self.checkBox_follow.isChecked():
            count += 1
        if self.checkBox_comment.isChecked():
            count += 1
        return count

    # 딜레이 시간 함수
    def delayTime(self): 
        delay_time = int(self.lineEdit_delay.text())
        if self.checkCnt() == 3:
            time.sleep(random.uniform(int(delay_time) / 3, int(delay_time) / 3 + 5))
        elif self.checkCnt() == 2:
            time.sleep(random.uniform(int(delay_time) / 2, int(delay_time) / 2 + 5))
        else: # 1
            time.sleep(random.uniform(int(delay_time), int(delay_time) + 5))

    # 댓글 체크박스 상태에 따른 활성화 함수
    def buttonStat(self):
        if self.checkBox_comment.isChecked():
            self.groupBox_Comments.setEnabled(True)
            self.groupBox_Comments_2.setEnabled(True)
        else:
            self.groupBox_Comments.setEnabled(False)
            self.groupBox_Comments_2.setEnabled(False)

    # 좋아요 함수
    def like(self): 
        if not self.checkBox_like.isChecked():
            logMsg("좋아요 작업 건너뛰기")
            return
        self.delayTime()
        driver.find_element_by_css_selector("._aamw ._abl-").click()
        logMsg("[{0}]번째 좋아요".format(i_cnt + 1))
        time.sleep(random.uniform(3,6))
        
    # 댓글 달기 함수   
    def comment(self): 
        if not self.checkBox_comment.isChecked():
            logMsg("댓글 작업 건너뛰기")
            return
        try:
            driver.find_element_by_css_selector(".xs3hnx8").click()
            time.sleep(random.uniform(5,10))

            random_message = self.randomMessage() # 랜덤메시지 함수에서 리턴값 가져오기

            driver.find_element_by_css_selector(".xs3hnx8").send_keys(random_message)

            self.delayTime()

            driver.find_element_by_css_selector("._aad0").click()
            logMsg("[{0}]번째 댓글 달기 : {1}".format(i_cnt + 1, random_message))

            driver.implicitly_wait(15)
            time.sleep(random.uniform(4,6))
        except Exception as e:
            logErr(str(e))
            logMsg("댓글이 비활성화 된 게시물입니다.")

    # 팔로우 함수
    def follow(self): 
        if not self.checkBox_follow.isChecked():
            logMsg("팔로우 작업 건너뛰기")
            return
        self.delayTime()
        driver.find_element_by_css_selector("._aar2 ._aade").click()
        logMsg("[{0}]번째 팔로우".format(i_cnt + 1))
        time.sleep(random.uniform(7,12))

    # 언팔로우 함수
    def unfollow(self):
        if self.comboBox_sup.currentIndex() == 0:
            if self.radioButton.isChecked():
                num = 2
            elif self.radioButton_2.isChecked():
                num = 3
            else:
                logMsg("필수 값 입력 누락! UI 창을 다시 확인 해주세요.")
                return
        else:
            logMsg("에러 발생!")
            return

        # 2 -> Unfollow unfollowers, 3 -> Unfollow following

        listToUnfollow = []
        if num == 2:
            for x in range(self.listWidget_unfollowers.count()):
                listToUnfollow.append(self.listWidget_unfollowers.item(x).text())
            logMsg("언팔로워를 언팔로우 합니다.")
        if num == 3:
            for x in range(self.listWidget_following.count()):
                listToUnfollow.append(self.listWidget_following.item(x).text())
            logMsg("팔로잉 하는 모든 계정을 언팔로우 합니다.")

        for idx, username in enumerate(listToUnfollow):
            url = 'https://www.instagram.com/' + str(username) 
            driver.get(url)
            driver.implicitly_wait(30)
            time.sleep(random.uniform(int(self.lineEdit_delay.text()), int(self.lineEdit_delay.text())+10))
            
            try: 
                if driver.find_element(By.CSS_SELECTOR, "._aade ._ab9p").is_displayed():
                    unfollowBtn1 = "._aade ._ab9p"
                    unfollowBtn2 = "._a9-_"
            except NoSuchElementException as e:
                    unfollowBtn1 = "._ab9x"
                    unfollowBtn2 = "div.x7r02ix.xf1ldfh.x131esax.xdajt7p.xxfnqb6.xb88tzc.xw2csxc.x1odjw0f.x5fp0pe > div > div > div > div:nth-child(8)"

            try:
                self.avoidFunction(idx)

                driver.find_element_by_css_selector(unfollowBtn1).click() # 팔로우 취소 창 접근
                time.sleep(random.uniform(10,30))

                driver.find_element_by_css_selector(unfollowBtn2).click() # 팔로우 취소 버튼 클릭
                logMsg("{0}/{1} 언팔로우 완료".format(idx + 1, len(listToUnfollow)))

                time.sleep(random.uniform(10,20))

            except Exception as e:
                logErr(str(e))
                logMsg("에러 발생! 60-100초 대기합니다.")
                time.sleep(random.uniform(60,100)) 

    # 유저 관리 함수
    def Management(self):
        if self.comboBox_sup.currentIndex() == 1:
            if self.radioButton.isChecked():
                num = 4
            elif self.radioButton_2.isChecked():
                num = 5
            else:
                logMsg("필수 값 입력 누락! UI 창을 다시 확인 해주세요.")
                return
        else:
            logMsg("에러 발생!")
            return

        # 4 -> Followers Management, 5 -> Following Management

        listToManage = []

        if num == 4:
            for x in range(self.listWidget_followers.count()):
                listToManage.append(self.listWidget_followers.item(x).text())
            logMsg("팔로워 관리를 시작합니다.")
        if num == 5:
            for x in range(self.listWidget_following.count()):
                listToManage.append(self.listWidget_following.item(x).text())
            logMsg("팔로잉 관리를 시작합니다.")

        for idx, username in enumerate(listToManage):

            global i_cnt
            i_cnt = idx

            url = 'https://www.instagram.com/' + str(username) 
            driver.get(url)
            driver.implicitly_wait(30)
            time.sleep(random.uniform(10,20))

            #Management Code here
            try:
                pic_list = driver.find_elements_by_css_selector("._aagw , ._aanf:nth-child(1) ._a6hd")
                pic_list = list(pic_list)
                driver.implicitly_wait(15)
                time.sleep(5)
                pic_list[0].click()
                driver.implicitly_wait(15)
                time.sleep(10)

                self.avoidFunction(idx)
                
                try: # Like Check
                    driver.find_element_by_css_selector("._aamw ._abl- ._abm1") # Didn't Liked return false
                    self.like()
                except NoSuchElementException as e:
                    logErr(str(e))
                    logMsg("이미 좋아요 한 게시물")
                except Exception as e:
                    logErr(str(e))
                    logMsg("좋아요 작업 실패")

                try: # Comment Check
                    commentchk = 0
                    listCommentUser = driver.find_elements_by_css_selector("._a9ym ._acaw") # Comment User Lists
                    for commentUser in listCommentUser:
                        if self.lineEdit_id.text() == commentUser.text:
                            logMsg("이미 댓글을 단 게시물")
                            commentchk = 1
                            break
                    if commentchk == 0:
                        self.comment()
                except Exception as e:
                    logErr(str(e))
                    logMsg("댓글 작업 실패")

                logMsg("다음 계정으로 이동 중 ...")
            except Exception as e:
                logErr(str(e))
                logMsg("에러 발생!, 다음 계정으로 이동 중 ...")

    # 다중 좋아요 함수
    def likeRepeat(self, like_cnt):
        username = driver.find_element_by_css_selector("._aasi ._aaqt").text
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])

        if username.find("인증됨") != -1:
            username = username[:username.find("인증됨")]
        
        driver.get("https://www.instagram.com/" + username)
        time.sleep(10)

        feed_cnt = int((driver.find_element_by_css_selector(".x2pgyrj > ._aade ._ac2a").text).replace(',', ''))
        logMsg("피드 수 : {0}".format(feed_cnt))
        feed_cnt -= 1 # like()에서 하나 눌러줄거기 때문
        like_cnt -= 1

        pic_list = driver.find_elements_by_css_selector("._aagw , ._aanf:nth-child(1) ._a6hd")
        pic_list = list(pic_list)
        driver.implicitly_wait(15)
        time.sleep(5)
        pic_list[0].click()
        driver.implicitly_wait(15)
        time.sleep(10)

        if feed_cnt < like_cnt:
            like_cnt = feed_cnt

        for i in range(like_cnt):
            driver.find_element_by_css_selector("._aaqg ._abl-").click() # 다음
            time.sleep(random.uniform(10,20))
            driver.find_element_by_css_selector("._aamw ._abl-").click() # 좋아요
            logMsg("다중 좋아요 작업, [{0}]번째 좋아요.".format(i + 2))
            time.sleep(random.uniform(10,20))
        
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    # 매크로 감지 피하기 함수
    def avoidFunction(self, cnt):
        if self.checkBox_avoidFunc.isChecked():
            randomNum = random.randint(20, 90)
            if (cnt+1) % 50 == 0:
                time.sleep(random.uniform(600,800))
                logMsg("매크로 감지 우회 기능 사용 중.. 600~800초 대기합니다.")
            elif (cnt+1) % randomNum == 0:
                time.sleep(random.uniform(180,300))
                logMsg("매크로 감지 우회 기능 사용 중.. 180~300초 대기합니다.")

# 로그 저장 함수
def logMsg(msg):
    f = open("./log/log.txt",'a')
    print(msg)
    textBrowser_msglog.append('[' + time.strftime('%H:%M:%S') + '] ' + msg)
    log = time.strftime('%x [%H:%M:%S] ') + msg + "\n"
    f.write(log)


# 에러 저장 함수
def logErr(msg):
    f = open("./log/error.txt",'a')
    print(msg)
    log = time.strftime('%x [%H:%M:%S] ') + msg + "\n"
    f.write(log)


#Main

if __name__ == "__main__" :
    
    app = QApplication(sys.argv)

    myWindow = WindowClass()

    app.setWindowIcon(QIcon(resource.icon))

    myWindow.show()
    app.exec_()