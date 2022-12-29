import asyncio
import logging
from asyncio.streams import StreamReader, StreamWriter
from collections import defaultdict
from enum import Enum
from hashlib import md5
from struct import Struct
from typing import Callable, Optional, Union

import db.db_messages as dbm
from db.abstract_db_connect import AbstractDbConnect
from db.pg_converters import PG_TYPES, python_types_convert_to_pg_params, string_in
from db.query_context import QueryContext

logger = logging.getLogger(__name__)

NULL_BYTE = b'\x00'


class CharType(Enum):
    i = 'i'
    ii = 'ii'
    ihihih = 'ihihih'
    h = 'h'    # noqa VNE001
    ih = 'ih'
    ci = 'ci'
    cccc = 'cccc'
    bh = 'bh'


class CustomDbError(Exception):
    pass


class CPack:
    """ Кодирует и декодирует данные в структуры C """

    def __init__(self, type_marker: CharType) -> None:

        # https://www.bestprog.net/ru/2020/05/08/python-module-struct-packing-unpacking-data-basic-methods-ru/#q03

        self._c_struct: Struct = Struct(f'!{type_marker.value}')

    def pack(self, data) -> bytes:
        return self._c_struct.pack(data)

    def unpack(self, data, offset: Optional[int] = None):
        if offset:
            return self._c_struct.unpack_from(data, offset)
        return self._c_struct.unpack_from(data)


packer_h = CPack(CharType.h)
packer_i = CPack(CharType.i)
packer_ihihih = CPack(CharType.ihihih)
packer_cccc = CPack(CharType.cccc)


class PgCoreConnect(AbstractDbConnect):
    # https://www.postgresql.org/docs/current/protocol-message-formats.html
    def __init__(    # noqa: CFQ002
        self,
        host: str,
        port: int,
        db_name: str,
        user: str,
        password: str,
        application_name=None,
        replication=None,
    ) -> None:
        """ Инициализация подключения к БД (без непосредственного подключения) """

        self._client_encoding = 'utf8'
        self._host = host
        self._port = port
        self._db = db_name
        self._user = user
        self._password = password

        self._query_context = QueryContext(None)

        self._postgres_types = defaultdict(lambda: string_in, PG_TYPES)

        self._encoded_password = self._encode_password(password)

        self._transaction_status = None

        self._encoded_init_params = self._encode_init_params({
            'user': user,
            'database': db_name,
            'application_name': application_name,
            'replication': replication,
        })

        self._encoded_user = self._encoded_init_params['user']

        self._message_handlers = {
            dbm.AUTHENTICATION_REQUEST: self._handle_AUTHENTICATION_REQUEST,
            dbm.PARAMETER_STATUS: self._handle_PARAMETER_STATUS,
            dbm.BACKEND_KEY_DATA: self._handle_BACKEND_KEY_DATA,
            dbm.CONNECTION_READY: self._handle_CONNECTION_READY,
            dbm.ROW_DESCRIPTION: self._handle_ROW_DESCRIPTION,
            dbm.DATA_ROW: self._handle_DATA_ROW,
            dbm.COMMAND_COMPLETE: self._handle_command_COMPLITE,
            dbm.PARSE_COMPLETE: self._handle_PARSE_COMPLETE,
            dbm.BIND_COMPLETE: self._handle_BIND_COMPLETE,
            dbm.PARAMETER_DESCRIPTION: self._handle_PARAMETER_DESCRIPTION,
            dbm.NO_DATA: self._handle_NO_DATA,
        }

        self._authenticate_handlers = {
            0: self._authenticate_nope,
            3: self._authenticate_by_plain_password,    # обработчик просто по-паролю
            5: self._authenticate_by_md5_password,    # обработчик по паролю (пароль+логин)
        }

    async def connect(self):
        """ Подключение к БД """
        self._reader, self._writer = await self._create_connection()
        await self._prepare_auth()
        await self.__run_while_not_command_in((dbm.CONNECTION_READY, dbm.ERROR_RESPONSE))

    async def run_query(self, stmt: str, *params):
        if len(params) == 0:
            query_context = await self.run_simple_query(stmt)
            return query_context
        else:
            params_ = params
            query_context = await self.run_query_with_params(stmt, params_)
            return query_context

    async def run_simple_query(self, stmt: str):
        """ Запуск на выполнение SQL-запроса """
        query_context: QueryContext = QueryContext(stmt)
        self._send_command_QUERY(stmt)
        await self._writer.drain()
        await self._handle_query_result_messages(query_context=query_context)

        return query_context

    async def run_query_with_params(self, stmt: str, vals: tuple = (), oids: tuple = ()):
        packer = CPack(CharType.i)
        query_context = QueryContext(stmt)

        self._send_command_PARSE(NULL_BYTE, stmt, oids)
        self._writer.write(dbm.SYNC + packer.pack(len(b'') + 4) + b'')
        await self._writer.drain()

        await self.__run_while_not_command_in((dbm.CONNECTION_READY, ),
                                              query_context=query_context)

        self._send_command_DESCRIBE_STATEMENT(NULL_BYTE)

        self._writer.write(dbm.SYNC + packer.pack(len(b'') + 4) + b'')

        await self._writer.drain()

        params = python_types_convert_to_pg_params(vals)

        self._send_command_BIND(NULL_BYTE, params)
        await self.__run_while_not_command_in((dbm.CONNECTION_READY, ),
                                              query_context=query_context)

        self._send_command_EXECUTE()

        self._writer.write(dbm.SYNC + packer.pack(len(b'') + 4) + b'')
        await self._writer.drain()
        await self.__run_while_not_command_in((dbm.CONNECTION_READY, ),
                                              query_context=query_context)

        return query_context

    async def close(self):
        """ Закртыие TCP-соединения с БД """
        self._writer.close()
        await self._writer.wait_closed()

    async def _create_connection(self) -> tuple[StreamReader, StreamWriter]:
        reader, writer = await asyncio.open_connection(self._host, self._port)

        return reader, writer

    async def __run_while_not_command_in(self, quit_commands: tuple, **kwarg):
        """ Выполняет комманды, пока не встретит указанные в агргументах """

        packer_ = CPack(CharType.ci)

        code_ = None
        while code_ not in quit_commands:    # крутим, пока не получим статус ГОТОВ или ОШИБКА

            code_, data_len_ = packer_.unpack(await self._reader.read(5))
            logger.debug(f'code: {code_}, data_len:{data_len_} ')

            payload_ = await self._reader.read(data_len_ - 4)
            logger.debug(f'payload:{payload_}')

            await self._message_handlers[code_](payload_, **kwarg)

    async def _prepare_auth(self):
        protocol = 196608
        packer_ = CPack(CharType.i)
        packed_val = packer_.pack(protocol)

        reauest_data = bytearray(packed_val)

        for key_, value_ in self._encoded_init_params.items():
            reauest_data.extend(key_.encode('ascii') + NULL_BYTE + value_ + NULL_BYTE)

        reauest_data.append(0)
        self._writer.write(packer_.pack(len(reauest_data) + 4))
        self._writer.write(reauest_data)
        await self._writer.drain()

    def _encode_password(self, password: Union[str, bytes]):
        """ Кодировка пароля в UTF-8 если пароль еще не кодирован """
        return password.encode('utf8') if isinstance(password, str) else password

    def _encode_init_params(self, init_params: dict[str, Union[str, None]]):
        """ кодировка значений по-умолчанию в UTF-8 """

        encoded_init_params: dict[str, bytes] = {}

        for key_, value_ in tuple(init_params.items()):
            if isinstance(value_, str):
                encoded_init_params[key_] = value_.encode('utf8')

        return encoded_init_params

    def _write_message(self, type_: bytes, data: bytes):
        """ Запись бинарных данных в сокет (без отправки) """

        try:
            self._writer.write(type_)
            packed_data_ = CPack(CharType.i).pack(len(data) + 4)
            self._writer.write(packed_data_)
            self._writer.write(data)
        except ValueError as e:
            if str(e) == 'write to closed file':
                raise CustomDbError('connection is closed')
            else:
                raise e
        except AttributeError:
            raise CustomDbError('connection is closed')

    async def _authenticate_nope(self, data):
        pass

    async def _authenticate_by_md5_password(self, data):
        """ Аутентификация по шифрованому паролю методом md5 + соль """

        unpacked_data = CPack(CharType.cccc).unpack(data, 4)

        salt = b''.join(unpacked_data)

        if self._password is None:
            raise CustomDbError('сервер требует MD5 аутентификацию пароля, но пароля нет, бро ')

        user_password = self._encoded_password + self._encoded_user
        md5_user_password = md5(user_password).hexdigest().encode('ascii')

        pwd = b'md5' + md5(string=md5_user_password + salt).hexdigest().encode('ascii')

        self._write_message(dbm.PASSWORD, pwd + NULL_BYTE)
        await self._writer.drain()

    async def _authenticate_by_plain_password(self):
        """ Аутентификация по паролю в открытом текстовом виде """

        if self._password is None:
            raise CustomDbError('Тербуется пароль, но отсутствует')

        self._write_message(dbm.PASSWORD, self._encoded_password + NULL_BYTE)
        await self._writer.drain()

    async def _handle_AUTHENTICATION_REQUEST(self, data):
        """ Обработка запросов на аутентификацию """

        # получение из ответа сервера ожидаеммый тип аутентификации
        auth_type: int = CPack(CharType.i).unpack(data)[0]
        logger.debug(f'auth_code: {auth_type}')

        # на основании типа выбираем обработчик из словаря и запускаем связанный метод
        await self._authenticate_handlers[auth_type](data)

    async def _handle_CONNECTION_READY(self, data, **kwargs):
        self._transaction_status = data

    async def _handle_ROW_DESCRIPTION(self, data, query_context: QueryContext):
        """ Функция-обработчика метаданных результата запроса """
        packer_h = CPack(CharType.h)
        packer_ihihih = CPack(CharType.ihihih)

        columns_count = packer_h.unpack(data)[0]
        idx = 2
        columns = []
        type_convert_functions: list[Callable] = []

        for _ in range(columns_count):
            name = data[idx:data.find(NULL_BYTE, idx)]
            idx += len(name) + 1
            field = dict(
                zip(
                    (
                        'table_oid',
                        'column_attrnum',
                        'type_oid',
                        'type_size',
                        'type_modifier',
                        'format',
                    ),
                    packer_ihihih.unpack(data, idx),
                ))

            field['name'] = name.decode(self._client_encoding)    # type: ignore

            idx += 18

            columns.append(field)

            oid = field['type_oid']
            convert_func = self._postgres_types[oid]
            type_convert_functions.append(convert_func)

        query_context.columns = columns
        query_context.type_converters = type_convert_functions

        if columns and query_context.rows is None:
            query_context.rows = []

    def _send_command_QUERY(self, stmt: str):
        """ запись запроса в поток (сокет) """

        self._write_message(dbm.QUERY, stmt.encode(self._client_encoding) + NULL_BYTE)

    async def _handle_DATA_ROW(self, data, query_context: QueryContext):
        logger.debug(data)

        idx = 2
        row = []
        packer = CPack(CharType.i)

        for type_converter in query_context.type_converters:
            value_len = packer.unpack(data, idx)[0]
            idx += 4
            if value_len == -1:
                value = None
            else:

                value = type_converter(
                    str(data[idx:idx + value_len], encoding=self._client_encoding))
                idx += value_len
            row.append(value)

        query_context.rows.append(row)    # type: ignore

    async def _handle_query_result_messages(self, **kwarg):
        await self.__run_while_not_command_in((dbm.CONNECTION_READY, ), **kwarg)

    async def _handle_command_COMPLITE(self, data, query_context: QueryContext):
        if self._transaction_status == dbm.IN_FAILED_TRANSACTION and query_context.stmt:
            sql = query_context.stmt.split()[0].rstrip(';').upper()
            if sql != 'ROLLBACK':
                raise CustomDbError('Не верный блок транзакций')

        values = data[:-1].split(b' ')
        try:
            rows_count = int(values[-1])
            if query_context.rows_count == -1:
                query_context.rows_count = rows_count
            else:
                query_context.rows_count += rows_count
        except ValueError:
            pass

    def _send_command_PARSE(self, statement_name_bin, statement, oids=()):
        packer_i = CPack(CharType.i)
        packer_h = CPack(CharType.h)

        value = bytearray(statement_name_bin)
        value.extend(statement.encode(self._client_encoding) + NULL_BYTE)
        value.extend(packer_h.pack(len(oids)))
        for oid in oids:
            value.extend(packer_i.pack(0 if oid == -1 else oid))

        self._write_message(dbm.PARSE, value)
        self._writer.write(dbm.FLUSH + packer_i.pack(len(b'') + 4) + b'')

    def _send_command_BIND(self, stmt_name: bytes, params: tuple):

        packer_h = CPack(CharType.h)
        packer_i = CPack(CharType.i)
        """ https://www.postgresql.org/docs/current/protocol-message-formats.html """
        retval = bytearray(NULL_BYTE + stmt_name + packer_h.pack(0) + packer_h.pack(len(params)))

        for param in params:
            if param is None:
                retval.extend(packer_i.pack(-1))
            else:
                param = param.encode(self._client_encoding)
                retval.extend(packer_i.pack(len(param)))
                retval.extend(param)

        retval.extend(packer_h.pack(0))

        self._write_message(dbm.BIND, retval)
        self._writer.write(dbm.FLUSH + packer_i.pack(len(b'') + 4) + b'')

    def _send_command_DESCRIBE_STATEMENT(self, stmt_name: bytes):
        packer_i = CPack(CharType.i)

        self._write_message(dbm.DESCRIBE, dbm.STATEMENT + stmt_name)
        self._writer.write(dbm.FLUSH + packer_i.pack(len(b'') + 4) + b'')

    def _send_command_EXECUTE(self):
        """ https://www.postgresql.org/docs/current/protocol-message-formats.html """

        packer_i = CPack(CharType.i)

        data_ = packer_i.pack(len(NULL_BYTE + packer_i.pack(0)) + 4)
        self._writer.write(dbm.EXECUTE + data_ + NULL_BYTE + packer_i.pack(0))
        self._writer.write(dbm.FLUSH + packer_i.pack(len(b'') + 4) + b'')

    async def _handle_PARAMETER_DESCRIPTION(self, *args, **kwarg):
        pass

    async def _handle_BIND_COMPLETE(self, *args, **kwarg):
        pass

    async def _handle_NO_DATA(self, *args, **kwargs):
        pass

    async def _handle_PARSE_COMPLETE(self, *args, **kwarg):
        pass

    async def _handle_PARAMETER_STATUS(self, *args):
        pass

    async def _handle_BACKEND_KEY_DATA(self, *args):
        pass

    async def __aenter__(self):
        await asyncio.sleep(0)
        return self

    async def __exit__(self):
        await self.close()
