from .NaverMail import NaverMail
import sys
import time
import os
from .utils import get_logger


class NaverMailWorker(NaverMail):
    def __init__(self, id: str, password: str) -> None:
        super().__init__(id, password)
        self.package_name = os.path.basename(__file__)
        self.logger = get_logger(
            "NaverMailWorker", 'data', prefix="NaverMailWorker")

    def _get_cookies(self) -> tuple[bool, str]:
        """ 셀레니움을 통해 쿠키를 생성한 후 저장한다.

        Returns:
            tuple[bool, str] : 저장에 성공하면   True, ''
                               실패하면 False, error 메세지
        """

        funcname = sys._getframe().f_code.co_name
        try:
            ok, result = self.get_cookies()
            if not ok:
                raise Exception(result)
            ok, result = self.save_cookies()
            if not ok:
                raise Exception(result)
            return True, ""
        except Exception as e:
            return False, f"[{self.package_name}/{funcname}] 쿠키 파일을 체크하는데 실패했습니다. {e}"

    def _check_cookies(self) -> tuple[bool, str]:
        """ 쿠키 상태를 체크한다

        Note:
            쿠키 파일을 체크 한 후에, 파일이 있으면 기존에 사용하던 쿠키를 가져온 후,
            네이버 메일함에 통신한 후, 쿠키가 살아있는지 확인한다.
            통신실패 (error code : NOLOGIN) 일 경우, 다시 쿠키를 생성한다.

        Returns:
            tuple[bool, str] : 저장에 성공하면   True, ''
                               실패하면 False, error 메세지
        """
        funcname = sys._getframe().f_code.co_name
        try:
            if os.path.isfile(os.path.join(self.FILEPATH, f"{self.id}_cookies.json")):
                ok, result = self.read_cookies()
                if not ok:
                    raise Exception(result)
                ok, result = self.get_mail_list()
                if ok:
                    pass
                elif not ok:
                    # 쿠키 유효성 체크
                    if 'NOLOGIN' in result:
                        ok, result = self._get_cookies()
                        if not ok:
                            raise Exception(result)
                else:
                    raise Exception(result)

            else:
                # 셀레니엄을 통해 쿠키를 가져온후 파일로 저장
                ok, result = self._get_cookies()
                if not ok:
                    raise Exception(result)

            return True, ""

        except Exception as e:
            return False, f"[{self.package_name}/{funcname}] 쿠키 파일을 체크하는데 실패했습니다. {e}"

    def _check_current_last_mail_no(self) -> tuple[bool, any]:
        """ 최근에 처리한 메일 번호확인한다.

        Note:
            self.last_mail_no(최근 처리한 메일 번호)가 없는경우,
            저장된 파일이 있으면, 저장된 파일을 읽어 self.last_mail_no를 설정한다.

        Returns:
            tuple[bool, any] : 저장에 성공하면 최근 처리한 메일 번호를 같이 리턴   True, int
                               실패하면 False, error 메세지
        """
        funcname = sys._getframe().f_code.co_name
        try:
            if not self.last_mail_no:
                # 저장된 파일 여부로 최초 메일 데이터 수집여부 확인
                if os.path.isfile(os.path.join(self.FILEPATH, f"{self.id}_last_mail_no.txt")):
                    # 파일이 있는 경우 메일 번호를 가져와서 사용
                    ok, result = self.read_last_mail_no()
                    if not ok:
                        raise Exception(result)
            return True, ""

        except Exception as e:
            return False, f"[{self.package_name}/{funcname}] 최근 처리한 메일 번호 체크에 실패했습니다. {e}"

    def run(self):
        """ 실행파일"""
        try:
            is_not_first = True
            ok, result = self._check_cookies()
            if not ok:
                raise Exception(result)
            ok, old_mail_no = self._check_current_last_mail_no()
            if not ok:
                raise Exception(old_mail_no)
            ok, mail_list = self.get_mail_list()
            if not ok:
                raise Exception(mail_list)

            if not self.last_mail_no:
                self.last_mail_no = mail_list[0]['mailSN']
                is_not_first = False

            # 최근 수집한 메일번호를 기준으로 메일 시작 index 찾음
            start_idx = [i for i in range(
                len(mail_list)) if mail_list[i]['mailSN'] == self.last_mail_no][0]
            # 수집이력이 있는경우, 중복 수집을 방지하기 위해, 1을 추가한다.
            start_idx += is_not_first
            for mail in mail_list[start_idx:]:
                time.sleep(0.3)
                ok, result = self.get_mail_content(mail['mailSN'])
                if not ok:
                    raise Exception(result)
                ok, result = self.save_mail_content(result['data'])
                if not ok:
                    raise Exception(result)
                # 중복 수집을 방지하기 위해, 마지막 메일 넘버 기록
                self.last_mail_no = mail['mailSN']
                ok, result = self.save_last_mail_no()
                if not ok:
                    raise Exception(result)

        except Exception as e:
            self.logger.error(e)
