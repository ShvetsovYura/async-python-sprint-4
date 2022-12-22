import asyncio
from asyncio.streams import StreamReader, StreamWriter
from enum import Enum
from hashlib import md5
from struct import Struct
from typing import Callable, Optional, Union

import db.db_messages as dbm

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


class InterfaceError(Exception):
    pass


class CPack:
    """ Кодирует и декодирует данные в структуры C """

    def __init__(self, type_marker: CharType) -> None:

        # https://www.bestprog.net/ru/2020/05/08/python-module-struct-packing-unpacking-data-basic-methods-ru/#q03

        self._c_struct: Struct = Struct(f'!{type_marker}')

    def pack(self, data) -> bytes:
        return self._c_struct.pack(data)

    def unpack(self, data, offset: Optional[int] = None):
        if offset:
            return self._c_struct.unpack_from(data, offset)
        return self._c_struct.unpack_from(data)


class DbConnect:

    def __init__(
        self,
        host: str,
        port: int,
        db_name: str,
        user: str,
        password: str,
        application_name=None,
        replication=None,
    ) -> None:
        self._client_encoding = 'utf8'
        self._host = host
        self._port = port
        self._db = db_name
        self._user = user
        self._password = password

        self._encoded_password = self._encode_password(password)
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
        }

    async def connect(self):
        self._reader, self._writer = await self._create_connection()
        await self._prepare_auth()
        packer_ = CPack(CharType.ci)

        code_ = None

        while code_ not in (b'Z', b'E'):
            code_, data_len_ = packer_.unpack(await self._reader.read(5))
            print(f'code: {code_}, data_len:{data_len_} ')
            cmd_ = await self._reader.read(data_len_ - 4)
            print(f"rd:{cmd_}")
            await self._message_handlers[code_](cmd_)

    async def _create_connection(self) -> tuple[StreamReader, StreamWriter]:
        reader, writer = await asyncio.open_connection(self._host, self._port)

        return reader, writer

    async def _prepare_auth(self):
        protocol = 196608
        packer_ = CPack('i')
        packed_val = packer_.pack(protocol)

        val = bytearray(packed_val)

        for key_, value_ in self._encoded_init_params.items():
            val.extend(key_.encode('ascii') + NULL_BYTE + value_ + NULL_BYTE)

        val.append(0)
        self._writer.write(packer_.pack(len(val) + 4))
        self._writer.write(val)
        await self._writer.drain()

    async def _close(self):
        self._writer.close()
        await self._writer.wait_closed()

    def _encode_password(self, password: Union[str, bytes]):
        return password.encode('utf8') if isinstance(password, str) else password

    def _encode_init_params(self, init_params: dict[str, Union[str, None]]):
        encoded_init_params: dict[str, bytes] = {}

        for key_, value_ in tuple(init_params.items()):
            if isinstance(value_, str):
                encoded_init_params[key_] = value_.encode('utf8')

        return encoded_init_params

    def _write_message(self, type_: bytes, data: bytes):
        try:
            self._writer.write(type_)
            packed_data_ = CPack('i').pack(len(data) + 4)
            self._writer.write(packed_data_)
            self._writer.write(data)
        except ValueError as e:
            if str(e) == 'write to closed file':
                raise InterfaceError('connection is closed')
            else:
                raise e
        except AttributeError:
            raise InterfaceError('connection is closed')

    async def _handle_AUTHENTICATION_REQUEST(self, data):

        # получение из ответа сервера ожидаеммый тип аутентификации
        auth_type: int = CPack('i').unpack(data)[0]
        print(f'auth_code: {auth_type}')
        if auth_type == 0:
            pass
        elif auth_type == 3:

            if self._password is None:
                raise InterfaceError('Тербуется пароль, но отсутствует')

            self._write_message(dbm.PASSWORD, self._encoded_password + NULL_BYTE)
            await self._writer.drain()

        elif auth_type == 5:

            unpacked_data = CPack('c', 4).unpack(data, 4)

            salt = b''.join(unpacked_data)

            if self._password is None:
                raise InterfaceError('сервер требует MD5 аутентификацию пароля, но пароля нет ')

            md5_user_password = md5(self._encoded_password +
                                    self._encoded_user).hexdigest().encode('ascii')

            pwd = b'md5' + md5(md5_user_password + salt).hexdigest().encode('ascii')

            self._write_message(dbm.PASSWORD, pwd + NULL_BYTE)
            await self._writer.drain()

    async def _handle_PARAMETER_STATUS(self, data):
        pass

    async def _handle_BACKEND_KEY_DATA(self, data):
        pass