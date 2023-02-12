import re
import sys
from TexSoup import TexSoup

def replace_lines(lines, l):
    for no in lines.keys():
        l = l.replace(str(no), str(lines[no]))

    return l

class Ptlogic:
    PRETEX_PLUGIN = True
    defines = [ "ptlogic", "ptconcl", "ptkdns" ]

    def compile(self, soup):
        # elements = list(soup.find_all("ptlogic"))
        # print("Elements:", elements)

        for element in soup.find_all("ptlogic"):
            source = str(element.string)

            for rule in [
                (r"->", r"\,\rightarrow\,"),
                (r"=>", r"\:\Rightarrow\:"),
                (r"==>", r"\:\Rightarrow\:"),
                (r"<-", r"\,\leftarrow\,"),
                (r"<==", r"\:\Leftarrow\:"),
                (r"~", r"\lnot"),
                (r"&", r"\,\wedge\,"),
                (r"and", r"\,\wedge\,"),
                (r"xor", r"\,\triangledown\,"),
                (r"\forall", r"all"),
                (r"all", r"\forall")]:
                source = source.replace(rule[0], " {"+rule[1]+"} ")

            rsource = "$"+source+"$"
            element.replace(TexSoup(rsource))

        for element in soup.find_all("ptconcl"):
            args = list(element.args)
            source = None
            option = ""

            if len(args) == 2:
                option = str(TexSoup(args[0]))
                source = args[1][0:]
            elif len(args) == 1:
                source = args[0][0:]
            else:
                print("error with ptconcl!")
                sys.exit(1)

            sentences = list(x for x in str(source)
                .replace("-C-", "\n\n-C-\n\n")
                .replace("-S-", "\n\n-S-\n\n")
                .split("\n") if x.strip())

            if option == "" or option == "l":
                option = "l"
            elif option == "center":
                option = "c"
            elif option == "right":
                option = "r"
            elif re.fullmatch(r"^\d+(\.\d+|)+[a-zA-Z]*$", option):
                option = "p{"+option+"}"

            output = r"\noindent\begin{tabular}{@{}" + option + r"@{}}" + "\n"
            line = ""

            for i in range(0, len(sentences)):
                sentences[i] = sentences[i].strip()

                if sentences[i] == "-C-":
                    output += line + " \\\\ \\hline\n"
                    line = ""
                elif sentences[i] == "-S-":
                    output += line + " \\\\ \n"
                    line = ""
                else:
                    line += sentences[i]

            if line.strip() != "-S-" and line.strip() != "-C-":
                output += line

            output += "\n"
            output += r"\end{tabular}"
            element.replace(TexSoup(output))

        for element in soup.find_all("ptkdns"):
            source = str(element.string)
            table = [] # s..., nr, sch, b, k
            premises = {}
            new_lines = []
            numbers = {}

            cnum = 0
            pnum = 0

            for line in source.split("\n"):
                line = line.strip()

                if line == "":
                    continue
                else:
                    cnum += 1

                if line.strip() == "-B-":
                    new_lines.append(None)
                    continue

                e = [x.strip() for x in line.split(",")]
                # 0 - line variable
                numbers[e[0]] = cnum

                # 1 - formula
                # 2 - reference
                refs = [x.strip() for x in e[2].split("&")]
                refstr = ", ".join(refs)

                # 3 - comment
                if e[3].lower() == "p":
                    premises[e[0]] = (pnum, cnum)
                    refs.append(e[0])
                    refs.append("<P>")
                    pnum += 1

                new_lines.append([
                    refs,
                    replace_lines(numbers, e[0])+
                    " & "+e[1]+" & "+
                    replace_lines(numbers, refstr)+
                    " & "+e[3]])

            premises_count = 0
            for line in new_lines:
                if "<P>" in line[0]:
                    premises_count += 1

            calculated_stars = []

            for line in new_lines:
                stars = "0"*premises_count

                if "<P>" not in line[0]:
                    for ref in line[0]:
                        if ref in list(premises.keys()):
                            stars = bin(int(stars, 2) | int(calculated_stars[premises[ref][1]-1], 2))[2:].zfill(premises_count)
                        elif ref in list(numbers.keys()):
                            stars = bin(int(stars, 2) | int(calculated_stars[numbers[ref]-1], 2))[2:].zfill(premises_count)
                else:
                    pos = premises[line[0][1]][0]
                    stars = stars[:pos] + "1" + stars[pos+1:]

                calculated_stars.append(stars)

                while len(stars) < premises_count:
                    stars += "0"

                table.append(stars.replace("0", " &").replace("1", " $\\ast$ &") + " " + line[1])

            source = "\\noindent\\begin{tabular"+"}{|"+(" c |"*premises_count)+" c | c | c | c |}\\hline"+(" $\\star$ &"*premises_count)+" \# & Schema & Bez. & K."+"\\\\\\hline\n"+"\n\\\\\\hline".join(table)+r"\\\hline\end{tabular}"
            element.replace(TexSoup(source))

        return soup