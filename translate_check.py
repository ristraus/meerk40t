"""
translate_check.py

Scans the source tree for translatable strings and compares them with the existing translation
of a given locale. Outputs a delta_{locale}.po file for review and integration.

Usage:
    python translate_check.py <locale>
    python translate_check.py <locale> -v   # for validation

Supported locales: de, es, fr, hu, it, ja, nl, pt_BR, pt_PT, ru, zh
"""

import os
import sys

import polib

IGNORED_DIRS = [".git", ".github", "venv", ".venv"]
LOCALE_LONG_NAMES = {
    "de": "German",
    "es": "Spanish",
    "fr": "French",
    "hu": "Hungarian",
    "it": "Italian",
    "ja": "Japanese",
    "nl": "Dutch",
    "pt_BR": "Portuguese (Brazil)",
    "pt_PT": "Portuguese (Portugal)",
    "ru": "Russian",
    "zh": "Chinese",
}
GETTEXT_PLURAL_FORMS = {
    "de": "nplurals=2; plural=(n != 1);",
    "es": "nplurals=2; plural=(n != 1);",
    "fr": "nplurals=2; plural=(n > 1);",
    "hu": "nplurals=2; plural=(n != 1);",
    "it": "nplurals=2; plural=(n != 1);",
    "ja": "nplurals=1; plural=0;",
    "nl": "nplurals=2; plural=(n != 1);",
    "pt_BR": "nplurals=2; plural=(n > 1);",
    "pt_PT": "nplurals=2; plural=(n != 1);",
    "ru": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
    "zh": "nplurals=1; plural=0;",
}


def lf_coded(s):
    """
    Converts a string to a format suitable for msgid in .po files.
    Escapes quotes and handles newlines.
    """
    if not s:
        return ""
    s = s.replace("\\", "\\\\")  # Escape backslashes
    s = s.replace('"', '\\"')  # Escape double quotes
    s = s.replace("\t", "\\t")  # Escape tab
    s = s.replace("\n", "\\n")  # Escape newlines
    s = s.replace("\r", "\\r")  # Escape newlines
    return s


def read_source():
    """
    Scans the source directory for translatable strings (_ ("...") ).
    Also reads additional strings from 'additional_strings.txt' if present.
    Returns:
        id_strings_source: List of unique msgid strings found in the source.
        id_usage: List of usage locations for each msgid.
    """
    id_strings_source = []
    id_usage = []
    sourcedir = "./"
    linecount = 0
    filecount = 0

    for root, dirs, files in os.walk(sourcedir):
        # Skip ignored directories
        if any(root.startswith(s) or root.startswith("./" + s) for s in IGNORED_DIRS):
            continue
        for filename in files:
            fname = os.path.join(root, filename)
            if not fname.endswith(".py"):
                continue
            pfname = os.path.normpath(fname).replace("\\", "/")
            filecount += 1
            localline = 0
            msgid_mode = False
            msgid = ""
            with open(fname, mode="r", encoding="utf-8", errors="surrogateescape") as f:
                while True:
                    linecount += 1
                    localline += 1
                    line = f.readline()
                    if not line:
                        break
                    while line:
                        line = line.strip()
                        if not line:
                            break
                        if msgid_mode:
                            # End of msgid
                            if line.startswith(")"):
                                # Escape quotes in msgid
                                idx = 0
                                while True:
                                    idx = msgid.find('"', idx)
                                    if idx == 0:
                                        msgid = "\\" + msgid
                                        idx += 1
                                    elif idx > 0:
                                        if msgid[idx - 1] != "\\":
                                            msgid = msgid[:idx] + "\\" + msgid[idx:]
                                            idx += 1
                                    else:
                                        break
                                    idx += 1
                                if msgid not in id_strings_source:
                                    id_strings_source.append(msgid)
                                    id_usage.append(f"#: {pfname}:{localline}")
                                else:
                                    found_index = id_strings_source.index(msgid)
                                    id_usage[found_index] += f" {pfname}:{localline}"
                                msgid_mode = False
                                msgid = ""
                                idx = 0
                                if idx + 1 >= len(line):
                                    line = ""
                                else:
                                    line = line[idx + 1 :]
                                continue
                            elif line.startswith("+"):
                                idx = 0
                                if idx + 1 >= len(line):
                                    line = ""
                                else:
                                    line = line[idx + 1 :]
                                continue
                            elif line.startswith("'"):
                                quote = "'"
                                startidx = 1
                                while True:
                                    idx = line.find(quote, startidx)
                                    if idx < 0:
                                        msgid_mode = False
                                        line = ""
                                        break
                                    if line[idx - 1] == "\\":  # escape character
                                        startidx = idx + 1
                                    else:
                                        break
                                msgid += line[1:idx]
                                if idx + 1 >= len(line):
                                    line = ""
                                else:
                                    line = line[idx + 1 :]
                                continue
                            elif line.startswith('"'):
                                quote = '"'
                                startidx = 1
                                while True:
                                    idx = line.find(quote, startidx)
                                    if idx < 0:
                                        msgid_mode = False
                                        line = ""
                                        break
                                    if line[idx - 1] == "\\":  # escape character
                                        startidx = idx + 1
                                    else:
                                        break
                                msgid += line[1:idx]
                                if idx + 1 >= len(line):
                                    line = ""
                                else:
                                    line = line[idx + 1 :]
                                continue
                            else:
                                msgid_mode = False
                                line = ""
                                break
                        else:
                            idx = line.find("_(")
                            if idx >= 0:
                                msgid_mode = True
                                msgid = ""
                                line = line[idx + 2 :]
                            else:
                                line = ""
                                break

    # Read additional strings from file if present
    fname = "additional_strings.txt"
    if os.path.exists(fname):
        additional_new = 0
        additional_existing = 0
        po = polib.pofile(fname, encoding="utf-8")
        for e in po:
            id_str = lf_coded(e.msgid)
            if not id_str:
                continue
            if e.comment:
                last_usage = e.comment
            else:
                last_usage = " ".join(
                    [f"{o_fname}:{o_lineno}" for o_fname, o_lineno in e.occurrences]
                )
            if id_str not in id_strings_source:
                id_strings_source.append(id_str)
                id_usage.append(f"#: {last_usage}")
                additional_new += 1
            else:
                found_index = id_strings_source.index(id_str)
                id_usage[found_index] += f" {last_usage}"
                additional_existing += 1

        print(
            f"Read additional strings from 'additional_strings.txt': {additional_new} new, {additional_existing} existing"
        )
    print(
        f"Read {filecount} files with {linecount} lines and found {len(id_strings_source)} entries..."
    )
    return id_strings_source, id_usage


def read_po(locale):
    """
    Reads all .po files for the given locale and extracts msgid/msgstr pairs.
    Returns:
        id_strings: List of msgid strings found in the .po files.
        pairs: List of (msgid, msgstr) tuples.
    """
    id_strings = []
    pairs = []
    po_dir = f"./locale/{locale}/LC_MESSAGES/"
    if not os.path.isdir(po_dir):
        print(f"Locale directory {po_dir} does not exist or is empty.")
        return id_strings, pairs
    try:
        po_files = [
            f for f in next(os.walk(po_dir))[2] if os.path.splitext(f)[1] == ".po"
        ]
    except StopIteration:
        print(f"Locale directory {po_dir} does not exist or is empty.")
        return id_strings, pairs
    for po_file in po_files:
        fname = po_dir + po_file
        po = polib.pofile(fname, encoding="utf-8")
        id_strings.extend([lf_coded(e.msgid) for e in po])
        pairs.extend([(e.msgid, lf_coded(e.msgstr)) for e in po])

    return id_strings, pairs


def compare(locale, id_strings, id_strings_source, id_usage):
    """
    Compares source msgids with those in the .po file and writes new ones to delta_{locale}.po.
    """
    counts = [0, 0, 0]
    with open(
        f"./delta_{locale}.po", "w", encoding="utf-8", errors="surrogateescape"
    ) as outp:
        for idx, key in enumerate(id_strings_source):
            if not key:
                continue
            counts[0] += 1
            if key in id_strings:
                counts[1] += 1
            else:
                counts[2] += 1
                outp.write(f"{id_usage[idx]}\n")
                last = ""
                lkey = ""
                for kchar in key:
                    if kchar == '"' and last != "\\":
                        lkey += "\\"  # escape the quote
                    lkey += kchar
                    last = kchar
                outp.write(f'msgid "{lkey}"\n')
                outp.write('msgstr ""\n\n')
    print(
        f"Done for {locale}: examined={counts[0]}, found={counts[1]}, new={counts[2]}"
    )


def validate_po_old(locale, id_strings_source, id_usage, id_pairs):
    """
    Writes a validated .po file for the locale, removing empty, duplicate, and unused entries.
    """

    def write_proper_po_header(outp, locale):
        outp.write(
            f"# {LOCALE_LONG_NAMES.get(locale, 'Unknown')} translation for Meerk40t\n"
        )
        outp.write("# Project-Homepage: https://github.com/meerk40t/meerk40t\n")
        outp.write('msgid ""\n')
        outp.write('msgstr ""\n')
        outp.write('"Project-Id-Version: Meerk40t"\n')
        outp.write('"Content-Type: text/plain; charset=UTF-8"\n')
        outp.write('"Content-Transfer-Encoding: 8bit"\n')
        outp.write('"Language-Team: Meerk40t Translation Team"\n')
        outp.write(f'"Language: {locale}"\n')
        outp.write('"X-Generator: translate_check.py"\n')
        plur = GETTEXT_PLURAL_FORMS.get(locale, "")
        if plur:
            outp.write(f'"Plural-Forms: {plur}"\n')
        outp.write("\n")

    written = 0
    ignored_empty = 0
    ignored_duplicate = 0
    ignored_unused = 0
    pairs = {}
    for msgid, msgstr in id_pairs:
        pairs.setdefault(msgid, []).append(msgstr)
    with open(
        f"./fixed_{locale}_meerk40t.po", "w", encoding="utf-8", errors="surrogateescape"
    ) as outp:
        write_proper_po_header(outp, locale)
        for msgid, msgstr_list in pairs.items():
            msgstr = next((m for m in msgstr_list if m), "")
            to_write = True
            if len(msgstr_list) > 1:
                ignored_duplicate += len(msgstr_list) - 1
            if msgstr == "":
                ignored_empty += 1
                to_write = False
            if msgid not in id_strings_source:
                ignored_unused += 1
                to_write = False
            if to_write:
                orgidx = id_strings_source.index(msgid)
                if orgidx < 0:
                    ignored_unused += 1
                    continue
                outp.write(f"{id_usage[orgidx]}\n")
                outp.write(f'msgid "{msgid}"\n')
                outp.write(f'msgstr "{msgstr}"\n\n')
                written += 1
    print(
        f"Validation for {locale} done: written={written}, ignored_empty={ignored_empty}, ignored_duplicate={ignored_duplicate}, ignored_unused={ignored_unused}"
    )


def validate_po(locale, id_strings_source, id_usage, id_pairs):
    po = polib.POFile()
    # create header
    po.metadata = {
        "Project-Id-Version": "Meerk40t",
        "Language": locale,
        "Language-Team": "Meerk40t Translation Team",
        "Content-Type": "text/plain; charset=UTF-8",
        "Content-Transfer-Encoding": "8bit",
        "X-Generator": "translate_check.py",
        "Plural-Forms": GETTEXT_PLURAL_FORMS.get(locale, ""),
        # Add any other metadata you need
        # …
    }
    seen = set()
    written = 0
    ignored_empty = 0
    ignored_duplicate = 0
    ignored_unused = 0
    for msgid, msgstr in id_pairs:
        t_msgid = lf_coded(msgid)
        if not msgstr or t_msgid not in id_strings_source or msgid in seen:
            if t_msgid not in id_strings_source:
                ignored_unused += 1
            elif not msgstr:
                ignored_empty += 1
            else:
                ignored_duplicate += 1
            continue
        entry = polib.POEntry(msgid=msgid, msgstr=msgstr)
        idx = id_strings_source.index(t_msgid)
        usage = id_usage[idx]
        if usage.startswith("#: "):
            usage = usage[3:]  # Remove the leading "#: "
        if usage:
            for loc in usage.split(" "):
                if ":" in loc:
                    file = loc.split(":")[0]  # Use only the file part
                    line = loc.split(":")[1]
                else:
                    file = loc.strip()
                    line = "1"
                entry.occurrences.append((file, line))
        po.append(entry)
        seen.add(msgid)
        written += 1
    po.save(f"./fixed_{locale}_meerk40t.po")
    print(
        f"Validation for {locale} done: written={written}, ignored_empty={ignored_empty}, ignored_duplicate={ignored_duplicate}, ignored_unused={ignored_unused}"
    )


def main():
    """
    Main entry point for the script.
    """
    args = sys.argv[1:]
    locales = ["de"]
    if args:
        locales = args
    if locales[0].lower() == "all":
        locales = [
            "de",
            "es",
            "fr",
            "hu",
            "it",
            "ja",
            "nl",
            "pt_BR",
            "pt_PT",
            "ru",
            "zh",
        ]
    validate = False
    if "-v" in args or "--validate" in args:
        validate = True
        locales = [loc for loc in locales if loc not in ("-v", "--validate")]

    print("Usage: python ./translate_check.py <locale>")
    print("<locale> one of de, es, fr, hu, it, ja, nl, pt_BR, pt_PT, ru, zh")
    print("Reading sources...")
    id_strings_source, id_usage = read_source()
    for loc in locales:
        try:
            id_strings, pairs = read_po(loc)
        except Exception as e:
            print(f"Error reading locale {loc}: {e}")
            continue
        if validate:
            print(
                f"Validating locale {loc} ({LOCALE_LONG_NAMES.get(loc, 'Unknown')})..."
            )
            validate_po(loc, id_strings_source, id_usage, pairs)
        else:
            print(
                f"Checking for new translation strings for locale {loc} ({LOCALE_LONG_NAMES.get(loc, 'Unknown')})..."
            )
            compare(loc, id_strings, id_strings_source, id_usage)


if __name__ == "__main__":
    main()
