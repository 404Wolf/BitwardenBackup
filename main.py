import json
import asyncio
import sys
import os
import bitwarden
import pyqrcode
from urllib.parse import urlparse
import threading
from tqdm import tqdm

"""
Bitwarden Vault to HTML Converter

Credit to:
    https://github.com/ionic-team/ionicons
    https://github.com/simple-icons/
for the icons

To use, just run main.py, and name your vault export "export.json"
"""

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# load config file
config = json.load(open("config.json"))

# make a directory for qr codes
if "qrCodes" not in os.listdir():
    os.mkdir("qrCodes")

# load in the icon path names
logos = os.listdir("icons")

# load in the export, and then create a bitwarden class instance of it
export = json.load(open("export.json"))
export = bitwarden.bitwarden(export) #, fetching=True


def findLogo(uris: list) -> str:
    """
    Find the path to a logo given a uri.

    Args:
        uris (list): list of uris to try to find a logo from, checked from first to last

    Returns:
        str: the logo name, or None if no logos were found for the uri
    """

    try:
        for uri in uris:
            services = (
                urlparse(uri).netloc.replace("www", "").split(".")
            )  # attempt to parse the url to find the company name
            for service in services[1:]:
                if len(service) <= 4:  # most company names are >4 characters
                    continue
                for logo in logos:  # check to see if there is a logo for it
                    if service in logo:
                        return logo  # return the logo file name
    except TypeError:
        return


def qrCodeGen(string: str, path, scale=4):
    """Generate and save a qr code"""
    # 1) convert list of things needed to generate qr code into string
    # 2) remove bad unicode characters; qr codes only support latin-1 characters
    # 3) generate the qr code
    # 4) save it as an svg file in qrCodes/<item-id>
    string = string.encode("latin-1", "ignore").decode("latin-1")
    qr = pyqrcode.create(string[1:-1].replace("None", "null"))
    qr.svg(path, scale=scale)


threads = []  # holder array for qr code gen threads

# first part of the output html
html = """
<html>
    <head>
        <link rel="stylesheet" type="text/css" href="styles.css"></link>
        <link rel="stylesheet" type="text/css" href="items.css"></link>
        <link rel="apple-touch-icon" sizes="180x180" href="favicons/apple-touch-icon.png">
        <link rel="icon" type="image/png" sizes="32x32" href="favicons/favicon-32x32.png">
        <link rel="icon" type="image/png" sizes="16x16" href="favicons/favicon-16x16.png">
        <link rel="manifest" href="favicons/site.webmanifest">
        <link rel="mask-icon" href="favicons/safari-pinned-tab.svg" color="#5bbad5">
        <meta name="msapplication-TileColor" content="#2d89ef">
        <meta name="theme-color" content="#ffffff">
    </head>
    <body>
"""

print("Generating html...")
for index, item in tqdm(enumerate(export.items)):
    qrString = [item.name, item.username, item.password]

    # if a favicon was retreived for the item, use it
    if item.favicon != None:
        favicon = item.favicon
    else: #  if no favicons were found for the item, use the unknown icon
        favicon = "assets/unknown.svg"

    # attempt to find a hand crafted logo
    logo = findLogo(item.uris)
    if logo != None: #  stick to the previously set favicon if none found
        favicon = f"icons/{logo}"

    # if there are fields for the item, generate a block for them
    notesRightMargin = "20px"  # if there is not a field block then the notes are below the qr code
    fieldsHtml = f"""<h4 style="border-color: rgb{tuple(config["colours"]["outlines"]["inner"])}">"""
    if (item.fields != None) or (item.type in ("card", "identity")):
        fields = []
        for field in item.fields:
            fields.append((field.name, field.value))

        if item.type == "card":
            fields += item.card.items()

        if item.type == "identity":
            fields += item.identity.items()

        if item.totp != None:
            fields.append(("TOTP", item.totp,))

        qrString.append(tuple(fields)) #  update the qr code string

        # append each field to the fieldsHtml string
        fieldsHtml += f"""<h4 class="card" style="border-color: rgb{tuple(config["colours"]["outlines"]["inner"])}" id="fields-box">"""
        for key, value in fields:
            fieldsHtml += f"""
                {key}:
                    <span style="color: rgb{tuple(config["colours"]["text"]["alt"])}">
                        {value}
                    </span><br>"""

        if len(tuple(item.fields)) < 5:
            notesRightMargin = "260px"  # if there are a lot of fields, the notes are below the qr code
        fieldsHtml += "</h4>" #  close the fields block
    else:
        fieldsHtml = "" #  there are no fields
        notesRightMargin = "260px"  # since there are no fields, the notes are to the left of the qr code 
    fieldsHtml += "</div>"

    # if there are notes for the item, generate a block for them
    if item.notes != None:
        item.notes = item.notes.replace("\n", "<br>")
        # if notes are a single line, then don't put the word "Notes:" above,
        # but rather put it on the same line
        if "<br>" in item.notes:
            notesExtraNewline = "<br>"
        else:
            notesExtraNewline = ""
        notesHtml = f"""
            <h4 class="card" style="border-color: rgb{tuple(config["colours"]["outlines"]["inner"])}; margin-right: {notesRightMargin}" id="notes-box">
                Notes: {notesExtraNewline} <span style="color: rgb{tuple(config["colours"]["text"]["alt"])}"> {item.notes} </span>
            </h4>"""
    else:
        notesHtml = ""

    # if there are any uris, then put the first uri found for the item to the right side of the title
    if len(item.uris) > 0:
        link = f"({urlparse(item.uris[0]).netloc})".replace("()", "")
    else:
        link = ""

    # if the password for the item has ever been pwned, write how many times
    if item.pwned > 0:
        pwnedMsg = (
            f"""(pwned <span> <b> {"{:,}".format(item.pwned)} </b> <span> times)"""
        )
        if item.pwned == 1:  # english grammer for singular
            pwnedMsg = pwnedMsg.replace("times", "time")
        pwnedColour = tuple(config["colours"]["text"]["pwned"])
    else:
        pwnedMsg = ""
        pwnedColour = tuple(config["colours"]["text"]["alt"])

    #  set up qr code generation thread
    threads.append(
        threading.Thread(
            target=qrCodeGen,
            args=(
                str(qrString),
                f"qrCodes/{item.id}.svg",
            ),
        )  # begin qr code generation in the background
    )
    threads[-1].start()

    # add item's html block to the output html
    html += f"""
        <div class="card" id="main-card">
            <img class="qrCode" style="background-color: rgb{tuple(config["colours"]["misc"]["qrCodeBackground"])};" src="qrCodes/{item.id}.svg" alt="QR Code for item">
            <div class="container">
                <div class="card" style="border-color: rgb{tuple(config["colours"]["outlines"]["inner"])}" id="header-box">
                    <h4>
                        <img class="favicon" alt="favicon" src="{favicon}">
                        <span class="type" style="border-color: rgb{tuple(config["colours"]["outlines"]["outer"])}" id="type-box">
                            <img class="type-icon" alt="Type of item" src="assets/{item.type}.svg">
                            {item.type.title()}
                        </span>
                        <span>
                            <b style="font-size: 20px">
                                {item.name}
                            </b>
                        </span>
                        <br>
                        <span>
                            <i style="color: rgb{tuple(config["colours"]["text"]["alt"])}; font-size: 14px">
                                {item.id}
                            </i>
                        </span>
                        <span style="color: rgb{tuple(config["colours"]["text"]["alt"])}" id="link">
                            {link}
                        </span>
                    </h4>
                </div>
                <div style="margin:25px"></div>
                <h4 class="card" style="border-color: rgb{tuple(config["colours"]["outlines"]["inner"])}" id="login-box">
                        Username:
                        <span style="color: rgb{tuple(config["colours"]["text"]["alt"])}">
                            {item.username}
                        </span>
                        <br>
                        Password: 
                        <span style="color: rgb{tuple(config["colours"]["text"]["alt"])}">
                            {item.password}
                        </span>
                        <span style="color: rgb{tuple(config["colours"]["text"]["alt"])}">
                            <i style="color: rgb{pwnedColour}">
                                {pwnedMsg}
                            </i>
                        </span>
                </h4>
                {fieldsHtml}
                {notesHtml}
            </div>
        </div>
        <div style="margin:15px"></div>"""

html += """
    </body>
</html>"""

# dump the output html
with open("output.html", "w") as output:
    output.write(html)

# wait for qr code generation to finish
for thread in threads:
    try:
        thread.join()
    except:
        pass
