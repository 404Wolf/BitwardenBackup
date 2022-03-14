# Bitwarden Backup Human-izer
## A program to convert a bitwarden json backup into sleek html

### How to use:
1. Get the [official bitwarden desktop app](https://bitwarden.com/download/), in order to export your vault as a json file
1. Open the bitwarden desktop app, and click `file > export vault`, making sure to choose `json` as the format.
1. Once you reenter your master password, choose to download the json export in the same file directory as this project's `main.py`, and rename the export to `export.json`. You should be left with an **unencrypted** json file. When you are finished, you will want to delete this file and empty your trash.
1. Open console, and run `main.py` by entering `python main.py`, or `python3 main.py`, depending on your operating system. If you get a `ModuleNotFound` error, type `pip install <name of module that was not found>`. Depending on how many items are in your vault, this process can take a considerable amount of time (sometimes minutes).
1. Open `output.html` in a web browser such as [chrome](https://www.google.com/chrome/), and print out the file, or save it as a pdf by clicking the `save as pdf` option under `printers`.
1. Delete the `qrCodes` folder, `output.html` file, and `export.json` file when you are done, and **empty your trash**! If you use a utility such as google drive backup and sync, do not put these files in a folder that syncs. These files contain unencrypted sensitive data.

### Use cases:
- Printing out the backup 
- Storing as a backup on a hard drive, in case bitwarden ever goes away in the future
- Having access to your vault without needing a device

### Future plans:
- TOTP 2FA QR code generation
- Folder support (colour coding, or small tab on right side to indicate folder name)
- Credit card image generation (for credit card type items, generate a picture of a credit card with the user's info on it)
- Automatic html to pdf conversion
- Mark/save where the user has printed up to, so they can only print new content
- Decrypt encrypted bitwarden json backups
- Fix inaccurate/broken progress bar

### Examples of html exports:
![html output example](https://gitlab.com/bread/BitwardenBackup/-/raw/ebc03d4d2ac5d7cc1be0ffb58c076856a497e416/demoImages/html.png)
![printing out html output example](https://gitlab.com/bread/BitwardenBackup/-/raw/ebc03d4d2ac5d7cc1be0ffb58c076856a497e416/demoImages/printing.png)

### Other images:
![exporting a bitwarden vault](https://gitlab.com/bread/BitwardenBackup/-/raw/ebc03d4d2ac5d7cc1be0ffb58c076856a497e416/demoImages/exportMenu.png)
![the popup to export a bitwarden vault](https://gitlab.com/bread/BitwardenBackup/-/raw/ebc03d4d2ac5d7cc1be0ffb58c076856a497e416/demoImages/exportPopup.png)
![json export example](https://gitlab.com/bread/BitwardenBackup/-/raw/ebc03d4d2ac5d7cc1be0ffb58c076856a497e416/demoImages/json.png)

### Trying it out:
If you just want to try out the script, you can find an example `export.json` and `output.html` file [here](https://gitlab.com/bread/BitwardenBackup/-/tree/main/demoImages).

### If you have any questions, contacts can be found at [techy.cc](https://www.techy.cc)
