#!/usr/bin/python
import sys
import os
import argparse
import tempfile
import shutil
import subprocess
import time
from pretexcompiler import pretex_compiler
from pathlib import Path

def error(message):
    print(message)
    sys.exit(1)

def latexmk(input_file, source_file, output_directory, other):
    # %OTHER% -pdf -outdir=%OUTDIR% %DOC%
    command = ['latexmk', other, "-file-line-error", "-interaction=nonstopmode", "-outdir="+output_directory, input_file]
    result = subprocess.run(command, stdout=subprocess.PIPE)
    output = result.stdout.decode("utf-8").replace("\\n", "\n").replace(input_file.replace(".tex", ""), source_file.replace(".tex", ""))
    print("Running:", " ".join(command))
    print(output)

    if result.returncode != 0:
        error("An error occured.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = 'PreTeX',
        description = 'Preprocessor for latexmk.')

    parser.add_argument('filename')
    parser.add_argument('-b', '--build_directory')
    parser.add_argument('-o', '--output_file')
    parser.add_argument('-p', '--pass_latexmk')

    args = parser.parse_args()

    infile = args.filename.strip() if not args.filename == None else args.filename
    outdir = args.build_directory.strip() if not args.build_directory == None else args.build_directory
    outfile = args.output_file.strip() if not args.output_file == None else args.output_file
    passlmk = args.pass_latexmk.strip() if not args.pass_latexmk == None else args.pass_latexmk

    if not passlmk == None:
        if passlmk.startswith("\""):
            passlmk = passlmk[1:]
        if passlmk.endswith("\""):
            passlmk = passlmk[:-1]
    else:
        passlmk = ""

    if not outdir == None:
        if not Path(outdir).exists():
            print("Creating", outdir+"...")
            os.mkdir(outdir)
        elif not Path(outdir).is_dir():
            error(outdir, "does not exist!")

    path = tempfile.mkdtemp()
    tmpname = Path(path).name
    tmpdir = path
    tmptex = tmpdir+"/"+tmpname+".tex"
    tmppdf = tmpdir+"/"+tmpname+".pdf"
    compiler_output = ""

    try:
        with open(tmptex, 'w') as tmp:
            try:
                print("Reading", infile+"...")
                source = "".join(open(infile).readlines())

                print("Compiling...")
                compiler_output = pretex_compiler(infile, source)
                tmp.write(compiler_output)
                tmp.close()

                # print(tmptex, "".join(open(tmptex).readlines()))
                latexmk(tmptex, infile, tmpdir, passlmk)

                if Path(tmppdf).exists():
                    open(outfile, "wb").write(open(tmppdf, "rb").read())

            except FileNotFoundError:
                error(infile, "not found!")
    finally:
        print("Write to...", infile+".out.tex")
        open(infile+".out.tex", 'w').write(compiler_output)

        print("Cleaning...")
        shutil.rmtree(tmpdir)
        print("All done.")