import logging.handlers
import os
import time
import fnmatch
from datetime import datetime, timedelta


def removefilter(dirpath: str, days: int = 10, filter: str = "*.*") -> None:
    """생성일자가 지정한 일수보다 지난 파일이거나 파일크기가 0인 로그파일 삭제

    Args:
        dirpath (str) : 파일 위치
        days (int) : 
        filter (str) : 필터 할 파일 포멧

    """
    fromtime = time.mktime((datetime.now() - timedelta(days=days)).timetuple())
    totime = time.mktime((datetime.now() - timedelta(days=1)).timetuple())

    # topdown : 상위폴더에서 하위폴더순으로 검색. 역순으로 원하면 False
    for base, dirs, files in os.walk(dirpath, topdown=False):
        if base == dirpath:
            for name in fnmatch.filter(files, filter):
                fn = os.path.realpath(os.path.join(base, name))
                mt = os.path.getmtime(fn)
                ct = os.path.getmtime(fn)

                if (ct < fromtime or os.path.getsize(fn) == 0) and totime > mt:
                    try:
                        os.remove(fn)
                        print("-"*3, fn, "."*10, "deleted.")
                    except PermissionError:
                        pass


def get_logger(name: str, path: str = '.',
               maxbyte: int = 5 * 1024 * 1024, prefix: str = "",
               removedays: int = 10) -> logging.Logger:
    """로그작성하는 유틸

    Args:
        name (str) : 가져올 로그 이름 
        path (str) : 저장할 파일 위치
        maxbyte (int) : 최대 크기
        postfix (str) : 저장할 파일 이름 뒤에 붙힐 텍스트
        removedays (int) : 삭제 기한

    Returns:
        logging.Logger 

    """
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        removefilter(path, removedays)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if len(logger.handlers) > 0:
        return logger  # Logger already exists

    fomatter = logging.Formatter(
        '%(filename)s|%(asctime)s|thread-%(thread)d|line-%(lineno)s|%(levelname)s > %(message)s')
    filename = f"{path}/{prefix}.log"

    fileHandler = logging.handlers.TimedRotatingFileHandler(
        filename=filename, when='midnight', interval=1, encoding='utf-8')

    # 자정마다 한 번씩 로테이션
    fileHandler.suffix = f'%Y%m%d'  # 1일이 지난 로그파일은 로그 파일명 뒤에 날짜붙이기
    fileHandler.setFormatter(fomatter)

    # logging.StreamHandler(sys.stdout)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(fomatter)
    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)

    logger.propagate = False  # 동일한로그가 여러번출력되지 않도록 하기위함
    setattr(logger, "path", path)
    logger.info("logger {} created.".format(filename))

    return logger
