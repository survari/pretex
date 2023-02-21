import sys
import os
import pathlib
import importlib
import time
from TexSoup import TexSoup

class Token:
    line = 0
    name = ""
    content = ""
    braces = False

def error(file, line, linestr, message):
    print(file + ":" + str(line) + ": " + message)
    print("l." + str(line) + " " + linestr)
    print("Output written on example.pdf (1 page, 11521 bytes).")
    print("Latexmk: Errors, so I did not complete making targets")
    sys.exit(1)

def check_braces(file, line, linestr, source, index, tokens, br_count):
    t = Token()
    nl = Token()
    nl.content = "\n"
    tmp = ""

    while index < len(source):
        tmp += source[index]
        linestr += source[index]

        if source[index] == "\n":
            tokens.append(nl)
            index += 1
            line += 1
            linestr = ""
            continue

        if source[index] == "{":
            br_count += 1
            index += 1
            t.line = line
            t.braces = True
            t.name = tmp

            t.content = check_braces(file, line, linestr, source, index, tokens, br_count)[4]
            tokens.append(t)

            tmp = ""
            continue

        elif source[index] == "}":
            br_count -= 1

        index += 1

    if br_count != 0:
        error(file, line, linestr, "too many { or }! ("+str(br_count)+")")

    return (tokens, br_count, line, linestr, tmp)

def parse(file, source):
    # res = check_braces(file, 1, "", source, 0, [], 0)

    # if res[1] != 0:
    #     error(file, res[2], res[3], "too many { or }! ("+str(res[1])+")")

    return TexSoup(source)

def load_plugin(file):
    path = pathlib.Path(file)

    module_name = path.name.replace(".py", "")
    module_path = str(path.absolute())

    print("Loading", module_name, "from", module_path, "...")

    # try:
    spec = importlib.util.spec_from_file_location(
        module_name,
        module_path)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    PluginClass = None

    # Inspect the module to find the first specified class
    for name, obj in module.__dict__.items():
        if isinstance(obj, type):
            # This is a class
            PluginClass = obj
            break

    if PluginClass != None:
        print("Warning: Could not load plugin from", file)

        if hasattr(PluginClass(), "PRETEX_PLUGIN") == True and PluginClass().PRETEX_PLUGIN == True:
            return PluginClass()

    # finally:
    #     print("Warning: Could not load plugin from", file)

    return None

class PreTexPluginBB: pass
def get_plugins(_directories):
    plugins = []
    directories = []

    print("Checking out directories...")
    for d in _directories:
        if pathlib.Path(d).exists():
            print(" - "+d)
            directories.append(d)

    for dir in directories:
        directory = pathlib.Path(dir).absolute()

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            if os.path.isfile(file_path) and filename.endswith(".py"):
                plugin = load_plugin(file_path)

                if plugin != None:
                    p = PreTexPluginBB()
                    p.PLUGIN = plugin
                    p.FILENAME = str(file_path)
                    plugins.append(p)

    return plugins

def pretex_compiler(file, source):
    soup = parse(file, source)
    defines = []
    plugins = []

    for p in get_plugins([
        os.environ.get("TEXMFHOME", ".")+"/pretex/",
        os.getcwd(),
        os.getcwd()+"/plugins",
        os.path.realpath(os.path.dirname(__file__))+"/plugins" ]):

        try:
            if p.PLUGIN.PRETEX_PLUGIN == None:
                continue
        except AttributeError:
            continue

        for d in p.PLUGIN.defines:
            if p.FILENAME in [x[0] for x in defines]:
                continue

            if d in [x[1] for x in defines]:
                print("Two plugins define", d+":")
                for d2 in defines:
                    if d == d2[1]:
                        print(" -", d2[0])

                sys.exit(1)
            else:
                defines.append((p.FILENAME, d))

        plugins.append(p)

    contains = True
    counter = 0
    counters = {}

    _start = time.time()
    while contains == True and counter < 10:
        contains = False
        counter += 1

        for d in defines:
            if ("\\"+d[1]) in str(soup):
                contains = True

                for p in plugins:
                    start = time.time()
                    tmp = TexSoup(str(p.PLUGIN.compile(soup, file)))
                    soup = tmp if tmp != None else soup
                    end = time.time()

                    if not p.FILENAME in counters:
                        counters[p.FILENAME] = 0

                    counters[p.FILENAME] += (end - start)

    for k in counters.keys():
        print("Finished", k, "plugin in", str(counters[k])[0:6], "seconds.")

    _end = time.time()
    print("Finished compiling in", _end - _start, "seconds.")
    return str(soup)