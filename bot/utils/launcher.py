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
ooooo ooooo                                       o8                                         
 888   888   ooooooo   oo ooo oooo    oooooooo8 o888oo ooooooooo8 oo oooooo                  
 888ooo888   ooooo888   888 888 888  888ooooooo  888  888oooooo8   888    888                
 888   888 888    888   888 888 888          888 888  888          888                       
o888o o888o 88ooo88 8o o888o888o888o 88oooooo88   888o  88oooo888 o888o                      
ooooooooooo o88              oooo        oooo        o88        oooooooooo               o8  
 888    88  oooo   oooooooo8  888ooooo    888  ooooo oooo        888    888   ooooooo  o888oo
 888ooo8     888  888ooooooo  888   888   888o888     888        888oooo88  888     888 888  
 888         888          888 888   888   8888 88o    888        888    888 888     888 888  
o888o       o888o 88oooooo88 o888o o888o o888o o888o o888o      o888ooo888    88ooo88    888o
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
