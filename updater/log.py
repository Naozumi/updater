import logging
import sys


class Logger:

    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10

    def __init__(self, filename, *, logging_level, datefmt=None, format=None):
        if not format:
            format = "---\n%(asctime)-19s ~ %(module)s:%(lineno)d ~ %(levelname)s: %(message)s"
        if not datefmt:
            datefmt = "%Y-%m-%d %H:%M:%S"
        logging.basicConfig(filename=filename, level=logging_level, datefmt=datefmt, format=format)

    @staticmethod
    def current_stack(skip=0):
        try:
            1/0
        except ZeroDivisionError:
            f = sys.exc_info()[2].tb_frame
        for i in range(skip + 2):
            f = f.f_back
        lst = []
        while f is not None:
            lst.append((f, f.f_lineno))
            f = f.f_back
        return lst

    @staticmethod
    def extend_traceback(tb, stack):
        """Extend traceback with stack info."""
        head = tb
        for tb_frame, tb_lineno in stack:
            head = FauxTb(tb_frame, tb_lineno, head)
        return head

    def full_exc_info(self):
        """Like sys.exc_info, but includes the full traceback."""
        t, v, tb = sys.exc_info()
        full_tb = self.extend_traceback(tb, self.current_stack(2))
        return t, v, full_tb

    @staticmethod
    def func(function, *args):
        """Return a string formatted as a function call."""
        return function+"("+", ".join(map(str, args))+")"

    @staticmethod
    def set_level(level):
        logging.basicConfig(level=level)

    def critical(self, msg, *args, exc_info=None, func=None, tb=None):
        if func:
            msg = self.func(msg, *args)
        if exc_info or tb:
            logging.critical(msg, exc_info=self.full_exc_info())
        else:
            logging.critical(msg)

    def debug(self, msg, *args, exc_info=None, func=None, tb=None):
        if func:
            msg = self.func(msg, *args)
        if exc_info or tb:
            logging.debug(msg, exc_info=self.full_exc_info())
        else:
            logging.debug(msg)

    def error(self, msg, *args, exc_info=None, func=None, tb=None):
        if func:
            msg = self.func(msg, *args)
        if exc_info or tb:
            logging.error(msg, exc_info=self.full_exc_info())
        else:
            logging.error(msg)

    def info(self, msg, *args, exc_info=None, func=None, tb=None):
        if func:
            msg = self.func(msg, *args)
        if exc_info or tb:
            logging.info(msg, exc_info=self.full_exc_info())
        else:
            logging.info(msg)

    def warning(self, msg, *args, exc_info=None, func=None, tb=None):
        if func:
            msg = self.func(msg, *args)
        if exc_info or tb:
            logging.warning(msg, exc_info=self.full_exc_info())
        else:
            logging.warning(msg)

    @staticmethod
    def unhandled(exc_type, value, traceback):
        logging.error("Unhandled Exception", exc_info=(exc_type, value, traceback))


class FauxTb(object):

    def __init__(self, tb_frame, tb_lineno, tb_next):
        self.tb_frame = tb_frame
        self.tb_lineno = tb_lineno
        self.tb_next = tb_next
