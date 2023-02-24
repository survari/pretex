import json
import re
import sys
from TexSoup import TexSoup

def error(file, line, linestr, message):
    print(file + ":" + str(line) + ": " + message)
    print("l." + str(line) + " " + linestr)
    print("Output written on example.pdf (1 page, 11521 bytes).")
    print("Latexmk: Errors, so I did not complete making targets")
    sys.exit(1)

def new_node(index):
    return {
        "index": index,
        "content": None,
        "options": [],
        "children": []
    }

def parse_node(index, string, rd=0):
    nodes = []
    n = new_node(index)

    tmp = ""
    last_state = ""
    state = "name" # | option | child

    while index < len(string):
        if state == "name":
            # print(state, "=>", tmp, nodes)

            if index+2 < len(string) and string[index] == "{" and string[index+1] == "{" and string[index+2] == ".":
                index += 3

                while index+2 < len(string) and not (string[index] == "." and string[index+1] == "}" and string[index+2] == "}"):
                    if string[index] == "~":
                        tmp += string[index+1]
                        index += 2
                        continue

                    tmp += string[index]
                    index += 1

                index += 3
                continue

            if string[index] == "{":
                if n["content"] == None:
                    n["content"] = tmp.strip()
                tmp = ""
                ret = parse_node(index+1, string, rd+1)

                for node in ret[1]:
                    n["children"].append(node)

                index = ret[0]
                state = "child"
                continue

            elif string[index] == "[":
                if n["content"] == None:
                    n["content"] = tmp.strip()
                tmp = ""
                state = "option"

            elif string[index] == "}":
                break

            elif string[index] == ",":
                if n["content"] == None:
                    n["content"] = tmp.strip()
                tmp = ""
                index += 1

                nodes.append(n)
                n = new_node(index)
                continue

        elif state == "option":
            tmp = ""

            while index < len(string):
                if string[index] == "]":
                    n["options"] = [x.strip() for x in tmp.strip("").split(",")]
                    tmp = ""
                    break

                tmp += string[index]
                index += 1

            if string[index] == "]":
                index += 1

            state = "name"
            continue

        elif state == "child":
            if string[index] == ",":
                nodes.append(n)
                n = new_node(index)
                index += 1

                tmp = ""
                state = "name"
                continue

            if string[index] == "}":
                break

        else:
            print("error parsing \\ptast:\n", string)
            sys.exit(1)

        tmp += string[index]
        index += 1

    if tmp.strip() != "" and n["content"] == None:
        n["content"] = tmp.strip()

    nodes.append(n)
    return (index + 1, nodes)

def make_tikz_from_tree(tree, child_count, child_index):
    if tree["content"] == None or len(tree["content"].strip()) == 0:
        return ""

    result = ""

    if len(tree["options"]) != 0 and child_index != None and child_count != None:
        preferred_position = "left"

        if child_count > 0 and child_index == 0:
            preferred_position = "right"

        if len(tree["options"]) > 1:
            result += "\edge node[" + ",".join(tree["options"][1:]) + "] {" + tree["options"][0] + "}; "
        else:
            result += "\edge node[ptredlabel,auto="+preferred_position+"] {" + tree["options"][0] + "}; "

    result += "[.{"+tree["content"]+"} "
    index = 0
    count = len(tree["children"])

    for c in tree["children"]:
        result += make_tikz_from_tree(c, count, index)
        index += 1

    result += "] "

    return result+"\n"

class Ptast:
    PRETEX_PLUGIN = True
    defines = ["ptast"]

    def compile(self, soup, file):
        for element in soup.find_all("ptast"):
            source = "" # str(element.string).strip()
            options = r"""sibling distance=0.5cm,
    level distance=1.75cm,
    growth parent anchor={north},
    nodes={anchor=north},
    empty/.style={draw=none},
    ptredlabel/.style={pos=0.8,font=\footnotesize\color{red!70!black}}"""

            if len(list(element.args)) == 1:
                source = str(element.string).strip()
            else:
                source = str(element.args[-1])
                options = str(element.args[0])

            tree = parse_node(0, source)
            # print(json.dumps(tree, indent=4))

            if tree[0] == None:
                error(file, soup.char_pos_to_line(element.position)[0], tree[1], "error parsing \\ptast.")
            else:
                tree = tree[1]

            rsource = ""

            for e in tree:
                rsource += r"\begin{tikzpicture}["+options+"]\n\\Tree" + make_tikz_from_tree(e, None, None) + r"\end{tikzpicture}"

            # print(rsource)
            element.replace(TexSoup(rsource))

        return soup