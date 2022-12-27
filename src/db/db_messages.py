# DB Message codes
NOTICE_RESPONSE = b'N'
AUTHENTICATION_REQUEST = b'R'    # запрос аутентификации
PARAMETER_STATUS = b'S'    # параметры сервера БД
BACKEND_KEY_DATA = b'K'
CONNECTION_READY = b'Z'    # инициализация закончена (подключение к серверу), готов к запросам
ROW_DESCRIPTION = b'T'
ERROR_RESPONSE = b'E'    # ошибка
DATA_ROW = b'D'
COMMAND_COMPLETE = b'C'
PARSE_COMPLETE = b'1'
BIND_COMPLETE = b'2'
CLOSE_COMPLETE = b'3'
PORTAL_SUSPENDED = b's'
NO_DATA = b'n'
PARAMETER_DESCRIPTION = b't'
NOTIFICATION_RESPONSE = b'A'
COPY_DONE = b'c'
COPY_DATA = b'd'
COPY_IN_RESPONSE = b'G'
COPY_OUT_RESPONSE = b'H'
EMPTY_QUERY_RESPONSE = b'I'

BIND = b'B'
PARSE = b'P'
QUERY = b'Q'
EXECUTE = b'E'
FLUSH = b'H'
SYNC = b'S'
PASSWORD = b'p'
DESCRIBE = b'D'
TERMINATE = b'X'
CLOSE = b'C'

IDLE = b'I'
IN_TRANSACTION = b'T'
IN_FAILED_TRANSACTION = b'E'
