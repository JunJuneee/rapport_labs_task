from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
import json
import sys
import platform
import requests
import traceback
import pyperclip
from time import strftime, localtime
from bs4 import BeautifulSoup


class NaverMail():
    def __init__(self, id: str, password: str) -> None:
        self.id = id
        self.password = password
        self.FILEPATH = 'data'
        self.HEADERS = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"}
        self.cookies = {}
        self.last_mail_no = None
        self.package_name = os.path.basename(__file__)

    def get_cookies(self) -> tuple[bool, any]:
        """ 셀레니움을 이용해 쿠키를 획득한다.

        Note:
            윈도우 사용자는 61행, 67행 주석을 풀고, 62행, 68행 주석으로 변경후 사용

        Returns:
            tuple[bool, str] : 저장에 성공하면 쿠키를 같이 리턴  True, dict
                               실패하면 False, error 메세지
        """
        funcname = sys._getframe().f_code.co_name
        try:
            driver = webdriver.Chrome()
            options = webdriver.ChromeOptions()
            options.add_argument("headless")  # 브라우저 감추기
            options.page_load_strategy = 'eager'
            options.add_argument("disable-gpu")
            options.add_argument("window-size=600,700")
            options.add_argument("window-position=0,0")
            options.add_argument("lang=ko_KR")  # 한국어!
            # unknown error: DevToolsActivePort file doesn't exist 에러로 인해 아래 옵션 추가
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument('--no-sandbox')
            options.add_argument("--remote-debugging-port=9222")  # 개발포트 지정
            # 드라이버 생성을 특정함수 안에서 하게 되면 함수가 종료될때 브라우저도 같이 종료방지
            options.add_experimental_option("detach", True)
            options.add_argument('--disable-logging')
            options.add_argument('--disable-extensions')
            # Headless 탐지막으려먼 user-agent 속성 다르게 추가
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36")

            driver.get(
                "https://nid.naver.com/nidlogin.login?mode=form&url=https://mail.naver.com/v2/folders/0/all")
            id_tag = driver.find_element("id", "id")
            pyperclip.copy(self.id)
            id_tag.click()
            if platform.system() == 'Windows':
                ActionChains(driver).key_down(Keys.CONTROL).send_keys(
                    'v').key_up(Keys.CONTROL).perform()
            else:
                ActionChains(driver).key_down(Keys.COMMAND).send_keys(
                    'v').key_up(Keys.COMMAND).perform()
            time.sleep(2)

            pwd_tag = driver.find_element("id", "pw")
            pyperclip.copy(self.password)
            pwd_tag.click()
            if platform.system() == 'Windows':
                ActionChains(driver).key_down(Keys.CONTROL).send_keys(
                    'v').key_up(Keys.CONTROL).perform()
            else:
                ActionChains(driver).key_down(Keys.COMMAND).send_keys(
                    'v').key_up(Keys.COMMAND).perform()
            time.sleep(2)

            driver.find_element(
                "css selector", "#login_keep_wrap > div.ip_check > span > label").click()
            driver.find_element("id", "log.login").submit()
            driver.implicitly_wait(3)
            if not driver.current_url.startswith("https://mail.naver.com/v2/folders/0/all"):
                raise Exception('capcha로 인한 로그인 실패')
            cookies = driver.get_cookies()
            cookies = {x['name']: x['value'] for x in cookies}
            self.cookies = cookies
            return True, cookies
        except Exception as e:
            print(traceback.format_exc())
            return False, f"[{self.package_name}/{funcname}] 셀레니엄으로 네이버 로그인에 실패했습니다. {e}"
        finally:
            if driver:
                driver.quit()

    def save_cookies(self) -> tuple[bool, str]:
        """ 쿠키를 파일로 저장한다.

        Returns:
            tuple[bool, str] : 저장에 성공하면   True, ''
                               실패하면 False, error 메세지
        """
        funcname = sys._getframe().f_code.co_name
        try:
            file_path = os.path.join(self.FILEPATH, f'{self.id}_cookies.json')
            with open(file_path, 'w') as f:
                json.dump(self.cookies, f, indent=4)

            return True, ""
        except Exception as e:
            return False, f"[{self.package_name}/{funcname}] 쿠키 파일 저장에 실패했습니다. {e}"

    def read_cookies(self) -> tuple[bool, any]:
        """ 저장된 쿠키 파일을 읽는다.

        Returns:
            tuple[bool, str] : 파일 읽기에 성공하면 쿠키를 같이 리턴  True, dict
                               실패하면 False, error 메세지
        """
        funcname = sys._getframe().f_code.co_name
        try:
            file_path = os.path.join(self.FILEPATH, f'{self.id}_cookies.json')
            with open(file_path, 'r') as f:
                cookies = json.load(f)
                self.cookies = cookies
            return True, self.cookies
        except Exception as e:
            return False, f"[{self.package_name}/{funcname}] 쿠키 파일을 읽어오는데 실패했습니다. {e}"

    def get_mail_list(self) -> tuple[bool, any]:
        """ 제일 메일 목록을 가져온다.

        Note:
            메일함에 메일이 없는경우 False를 리턴해서, 다음 프로세스를 타지 않음

        Returns:
            tuple[bool, any] : 메일 목록 조회 성공시, 목록 리스트 같이 반환  True, list
                               실패하면 False, error 메세지
        """
        funcname = sys._getframe().f_code.co_name
        try:
            page = 1
            mail_list = []
            url = f"https://mail.naver.com/json/list?folderSN=-1&page={page}&viewMode=time&previewMode=1&sortField=1&sortType=1&u={self.id}"
            res = requests.post(url, cookies=self.cookies,
                                headers=self.HEADERS).json()
            if res['Result'] == "FAIL":
                raise Exception(res['LoginStatus'])
            mail_list.extend(res['mailData'])
            for page in range(1, res['totalCount']//res['pageSize']+2):
                url = f"https://mail.naver.com/json/list?folderSN=-1&page={page}&viewMode=time&previewMode=1&sortField=1&sortType=1&u={self.id}"
                res = requests.post(url, cookies=self.cookies,
                                    headers=self.HEADERS).json()
                mail_list.extend(res['mailData'])
            if not mail_list:
                return False, "메일이 존재하지 않습니다."
            return True, mail_list
        except Exception as e:
            return False, f"[{self.package_name}/{funcname}] 마지막 메일 넘버를 가져오는데 실패했습니다. {e}"

    def read_last_mail_no(self) -> tuple[bool, any]:
        """ 파일로 저장된 최근에 처리한 메일 번호를 가져온다.

        Returns:
            tuple[bool, str] : 파일 읽기에 성공하면 최근에 처리한 메일 번호를 같이 리턴  True, int
                               실패하면 False, error 메세지
        """
        funcname = sys._getframe().f_code.co_name
        try:
            # raise Exception('tttes')
            file_path = os.path.join(
                self.FILEPATH, f'{self.id}_last_mail_no.txt')
            with open(file_path, 'r') as f:
                last_mail_no = int(f.readline())
                self.last_mail_no = last_mail_no
            return True, last_mail_no
        except Exception as e:
            return False, f"[{self.package_name}/{funcname}] last_mail_no을 읽어오는데 실패했습니다. {e}"

    def save_last_mail_no(self) -> tuple[bool, str]:
        """ 최근에 처리한 메일 번호를 파일로 저장한다.

        Returns:
            tuple[bool, str] : 저장에 성공하면   True, ''
                               실패하면 False, error 메세지
        """
        funcname = sys._getframe().f_code.co_name
        try:
            if self.last_mail_no:
                file_path = os.path.join(
                    self.FILEPATH, f'{self.id}_last_mail_no.txt')
                with open(file_path, 'w') as f:
                    f.write(str(self.last_mail_no))
            return True, ""
        except Exception as e:
            return False, f"[{self.package_name}/{funcname}] last_mail_no을 읽어오는데 실패했습니다. {e}"

    def get_mail_content(self, mail_no: int, mail_box_type: int = -1) -> tuple[bool, any]:
        """네이버 메일 내용을 가져온다

        Note:
            해당 메일 번호만 조회 하는것이 아니라,
            해당 메일보다 최신의 메일 번호를 반환하여, 
            다음번 조회 대상으로 변경하기 위해 같이 리턴한다.


        Args:
            mail_no (int) : 조회할 메일 번호
            mail_box_type (int) : 메일함 종류 : 전체메일 : -1, 받은메일함 : 0, 보낸메일함 : 1, 임시보관함 : 3, 내게쓴메일함 : 6


        Returns:
            tuple[bool, any] : 성공하면 데이터와, 이전 메일 번호를 리턴한다   True, dict
                               실패하면 False, error 메세지

        """
        funcname = sys._getframe().f_code.co_name
        result = {"data": [], "prev_mail_no": None}
        try:
            url = "https://mail.naver.com/json/read"
            data = {"mailSN": mail_no, "folderSN": mail_box_type}
            res = requests.post(
                url, data=data, headers=self.HEADERS, cookies=self.cookies).json()
            if res['Result'] != "OK":
                raise Exception(res['Message'])

            mail_info = res['mailInfo']
            subject = f"subject : {mail_info['subject']}"
            mail_from = f"from : {mail_info['from']['email']}"
            mail_to_list = ",".join([x['email'] for x in mail_info['toList']])
            mail_to = f"to : {mail_to_list}"
            mail_cc_list = ",".join([x['email'] for x in mail_info['ccList']])
            mail_cc = f"cc : {mail_cc_list}"
            receivedTime = strftime(
                '%Y-%m-%d %I:%M:%S %p',  localtime(mail_info['receivedTime']))
            # 내용만 파싱한다
            soup = BeautifulSoup(res['mailInfo']['body'], "html.parser")
            body = f"body : {' '.join(soup.stripped_strings)}"

            mail_content = [subject, mail_from, mail_to,
                            mail_cc, receivedTime, body, '\n']
            result['data'] = mail_content
            if res["prevMailData"]:
                result['prev_mail_no'] = res["prevMailData"]['mailSN']
            return True, result

        except Exception as e:
            return False, f"[{self.package_name}/{funcname}] 네이버에서 메일 내용을 가져오는데 실패했습니다. {e}"

    def save_mail_content(self, mail_content: list[str]) -> tuple[bool, str]:
        """네이버 메일 내용을 파일로 저장한다.

        Args:
            mail_content (list[str]) : 파일에 작성할 이메일 내용

        Returns:
            tuple[bool, str] : 저장에 성공하면   True, ''
                               실패하면 False, error 메세지

        """
        funcname = sys._getframe().f_code.co_name
        try:
            text_file_path = os.path.join(
                self.FILEPATH, f'{self.id}_mail.txt')
            texts = ""
            if os.path.isfile(text_file_path):
                with open(text_file_path, 'r', encoding='utf-8') as f:
                    texts = f.readlines()
            with open(text_file_path, 'w', encoding='utf-8') as f:
                f.writelines('\n'.join(mail_content))
                f.writelines(''.join(texts))
            return True, ""
        except Exception as e:
            return False, f"[{self.package_name}/{funcname}] 메일을 파일로 저장하는데 실패했습니다. {e}"
