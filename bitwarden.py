import asyncio
from pyfavicon import Favicon
from urllib.parse import urlparse
import hashlib
import aiohttp
from contextlib import suppress
import random
import json
from tqdm import tqdm


agents = json.load(open("agents.json"))


class folder:
    """A bitwarden folder"""

    def __init__(self, folder: dict) -> None:
        self.name = folder["name"]
        self.id = folder["id"]


class field:
    """Item field information."""

    def __init__(self, field: dict) -> None:
        self.name = field["name"]
        self.value = field["value"]
        self.type = field["type"]


class item:
    """
    A specific bitwarden item.

    Attributes:
        id {str}: item's id
        org {str or None}: item's organization
        folder {folder}: item's folder (or None)
        type {str}: item type ("login", "card", "identity", or "note")
        reprompt {bool}: reprompt for master password upon viewing
        name {str}: name of item
        notes {str}: notes for item
        favorite {bool}: favorited or not
    """

    def __init__(self, item: dict) -> None:
        self.id = item["id"]  # item id
        self.org = item["organizationId"]  # item's organization
        self.folder = item["folderId"]  # item's folder (or None)

        # item type
        self.type = item["type"]
        if self.type == 1:
            self.type = "login"
        elif self.type == 2:
            self.type = "note"
        elif self.type == 3:
            self.type = "card"
            self.card = item["card"]
        elif self.type == 4:
            self.type = "identity"
            self.identity = item["identity"]
        else:
            raise TypeError("Invalid item type")

        self.reprompt = item["reprompt"]  # reprompt for master password
        self.name = item["name"]  # name of item
        self.notes = item["notes"]  # notes for item
        self.favorite = item["favorite"]  # favorited or not

        self.uris = []
        if (self.type == "login") and ("uris" in item["login"]):
            self.uris = [
                _uri["uri"] for _uri in item["login"]["uris"]
            ]  # links for item

        if "login" in item:
            self.username = item["login"]["username"]
            self.password = item["login"]["password"]
            self.totp = item["login"]["totp"]
        else:
            self.username = None
            self.password = None
            self.totp = None

        if "fields" in item:
            self.fields = (field(_field) for _field in item["fields"])
        else:
            self.fields = None

        self.collections = item["collectionIds"]  # collections item belongs to, or None

        self.favicon = None
        self.pwned = 0


class bitwarden:
    """
    Content of a bitwarden export

    Args:
        export {dict}: the bitwarden export dict (unencrypted only)
        fetching {bool}: fetch favicons/check if passwords have been pwned

    Attributes:
        encrypted {bool}: whether the export is encrypted or not
        folders {list}: instances of folder class for folders found in the export
        items {list}: instances of item class for items found in the export
    """

    def __init__(self, export: dict, fetching=False) -> None:
        self.encrypted = export["encrypted"]  # vault is/isn't encrypted

        self.folders = {}
        for _folder in export["folders"]: #_folder because folder is taken (it's a class)
            id = _folder["id"]
            _folder = folder(_folder)
            self.folders[id] = _folder

        self.items = [item(_item) for _item in export["items"]]  # items in vault

        if fetching:  # fetch favicon / check if passwords have been pwned
            asyncio.run(self.fetches())

        #  turn typeString into type's order-number
        def typeOrder(itemType: str):
            if itemType == "identity":
                return 0
            elif itemType == "card":
                return 1
            elif itemType == "note":
                return 2
            elif itemType == "login":
                return 3
            else:
                return 4

        # sort by item type
        self.items = tuple(
            sorted(self.items, key=lambda item: typeOrder(item.type), reverse=False)
        )

    async def fetches(self) -> None:
        async def favicon(uris: list) -> str:
            """
            Get a direct link to the favicon of a given link

            Scans for favicons for the input link, and returns the largest one

            Args:
                uris {list}: the various uris of the item
            """

            if not isinstance(uris, list):
                return  # uris needs to be a list

            for uri in uris:
                # create instance of pyfavicon.Favicon() class
                faviconManager = Favicon(
                    headers={
                        "DNT": "1",  # if supported ask the website to not track us
                        "User-Agent": random.choice(agents),  # random human/browser-looking user agent
                    },
                )

                try:
                    # clean up link before grabbing favicon
                    uri = urlparse(uri).geturl()
                    if "http" not in uri:
                        uri = "https://" + uri
                    icons = await faviconManager.from_url(uri)

                    # return largest favicon out of all found
                    largest_icon = icons.get_largest()

                    # return the favicon's link, or None if no favicon links were found
                    if largest_icon != None:
                        return largest_icon.__dict__["link"]
                except:
                    return

        async def pwned(password: str, session: aiohttp.ClientSession) -> int:
            """
            Get how many times the password has been leaked.

            Args:
                password {str}: the password to scan breaches for
                session {aiohttp.ClientSession}: a live aiohttp client session object

            Returns:
                str: how many times the password has shown up in breaches
            """

            if password != None:
                # create sha1 hash of password for query
                sha1 = str(password).encode("utf-8")
                sha1 = hashlib.sha1(sha1)
                sha1 = sha1.hexdigest()

                # split sha1 hash into prefix and suffix
                sha1Prefix = sha1[:5].upper()
                sha1Suffix = sha1[5:].upper()

                # 1) send our sha1 hashed password's prefix to pwnedpasswords api
                # 2) pwnedpasswords api returns pwned counters for all possible suffixes
                # 3) we will scan the list to find our sha1 hashed password's suffix
                # 4) if it is not in the list returned, we have never been pwned
                async with session.get(
                    "https://api.pwnedpasswords.com/range/" + sha1Prefix,
                    headers={"User-Agent": "Bitwarden Vault Password Scanner"},
                ) as resp:
                    data = await resp.text()
                    data = data.split("\n")
                    data = map(lambda line: line.split(":"), data)

                    for querySha1Suffix, count in data:
                        if sha1Suffix == querySha1Suffix:
                            return int(
                                count
                            )  # we have been pwned, return how many times

            return 0  # if we were not pwned, return 0 for the pwned counter

        tasks = []  # array for fetch tasks

        async with aiohttp.ClientSession() as session:
            # create task for fetching favicon/checking if password is pwned for each item

            print("Fetching favicons and checking passwords against haveibeenpwned api")
            for item in tqdm(self.items):
                item.favicon = asyncio.create_task(favicon(item.uris))
                tasks.append(item.favicon)

                if (
                    "password" in item.__dict__
                ):  # if the item does not have a password, do not bother checking if "None" has been pwned
                    item.pwned = asyncio.create_task(pwned(item.password, session))
                    tasks.append(item.pwned)

                await asyncio.sleep(0.01)  # prevent pwned api ratelimiting

            # if there are any tasks that were created for the item then wait them out
            if len(tasks) > 0:
                print("Waiting for fetches to complete...")
                await asyncio.wait(tasks, timeout=4)

            for item in self.items:
                try:  # faivcon will just be the default if it fails to fetch
                    item.favicon = item.favicon.result()
                except:
                    item.favicon = None
                try:  # assumed not pwned if pwn checking fails
                    with suppress(AttributeError):
                        item.pwned = item.pwned.result()
                except:
                    item.pwned = 0