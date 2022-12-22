import asyncio

from db.connect import DbConnect


async def main():
    con = DbConnect(host='localhost',
                    port=5432,
                    db_name='dev_db',
                    user='app',
                    password='123qwe', application_name='hoho')
    await con.connect()


if __name__ == '__main__':
    asyncio.run(main())
