import os
import glob
import asyncio
import argparse
from itertools import cycle

from pyrogram import Client
from better_proxy import Proxy

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.registrator import register_sessions

banner = """

__$$$$$______________________________________$$$
__$$____$$$_______$$$$$$_$$$_$$$$$______$$$$___$
__$_$$_____$$$$$$__________________$$$$$$_____$$
__$___$__________$___________________________$__$
__$____$___________________________________$$___$
__$______$$_______________________________$_____$
__$_______$____________________________$$_______$
__$______$________________________________$_____$
___$____$__________________________________$___$
__$$___$____________________________________$___$
__$_$$$______________________________________$_$
_$___$________________________________________$$_$
_$________________$$$$$$____$$$$$$______________$_$
$__$____________$$$$$$$$____$$$$$$$$____________$_$
$__$__________$$__$$$$$$____$$$____$$$$_________$_$
$_$$________$$$_$$$__$$$____$$___$$$_$$$_________$_$
$_$$________$$_$$$$$$_$______$_$$$$$$$$_$_______$$_$
$_$$______$__$_$$$$_$$________$$_$$$$$_$__$_____$$_$
$_$$$____$$$_$$_$$$_$$$______$$$__$$$_$_$_$____$$$_$
$_$_$____$_$$__$___$$$________$$$___$__$$_$____$_$_$
$_$$_$__$___$$___$$$$$________$$$$$___$$$__$__$__$_$
_$_$_$_$$___$$$$_$$$$$________$$$$__$$$$___$____$_$
__$_$_$$______$$__$$_$________$$$__$$$___$__$$$$_$
___$$$$____$___$$____$________$___$$$___$______$
_____$$$$______$$____$________$___$$$_______$$
_______$$$$____$$___$__________$___$$______$
_________$$____$$___$__________$___$$____$$
___________$$_$$$___$__________$___$$_$$$
______________$_$___$__________$___$_$
_______________$$___$__________$___$$
________________$___$_$$$$$$$$_$___$
________________$___$$$$$$$$$$$$___$
_________________$__$$$$$$$$$$$$__$
__________________$_$$$$$$$$$$$$_$
"""
options = """
Select an action:

    1. Create session
    2. Run clicker
"""


def get_session_names() -> list[str]:
    session_names = glob.glob('sessions/*.session')
    session_names = [os.path.splitext(os.path.basename(file))[0] for file in session_names]

    return session_names


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file='./proxies.txt', encoding='utf-8-sig') as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies


async def get_tg_clients() -> list[Client]:
    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [Client(
        name=session_name,
        api_id=settings.API_ID,
        api_hash=settings.API_HASH,
        workdir='sessions/',
        plugins=dict(root='bot/plugins')
    ) for session_name in session_names]

    return tg_clients


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--action', type=int, help='Action to perform')

    print(banner)

    logger.info(f"Detected {len(get_session_names())} sessions | {len(get_proxies())} proxies")

    action = parser.parse_args().action

    if not action:
        print(options)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ['1', '2']:
                logger.warning("Action must be 1 or 2")
            else:
                action = int(action)
                break

    if action == 1:
        await register_sessions()
    elif action == 2:
        tg_clients = await get_tg_clients()

        await run_tasks(tg_clients=tg_clients)


async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    tasks = [asyncio.create_task(run_tapper(tg_client=tg_client, proxy=next(proxies_cycle) if proxies_cycle else None))
             for tg_client in tg_clients]

    await asyncio.gather(*tasks)
