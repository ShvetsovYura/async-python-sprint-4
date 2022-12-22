import asyncio
import logging
import logging.config

import yaml

from db.connect import DbConnect


async def main():
    con = DbConnect(host='localhost',
                    port=5432,
                    db_name='dev_db',
                    user='app',
                    password='123qwe',
                    application_name='hoho')
    await con.connect()


if __name__ == '__main__':
    with open('log-config.yml', 'r') as stream:
        cfg_ = yaml.safe_load(stream)
        logging.config.dictConfig(cfg_)

    asyncio.run(main())
