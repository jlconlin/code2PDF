
import argparse
import os
import shutil
import subprocess
import tempfile
import textwrap

import pygments
import pygments.lexers
import pygments.formatters


def findSourceFiles(path, extensions):
    """
    Return a list of absoluate paths to found source files.

    path: Where to search for the source code
    extensions: List of file extensions defining source code
    """
    sourceFiles = []
    for root, dirs, files in os.walk(path):
        for F in files:
            for ext in extensions:
                if F.endswith(ext):
                    sourceFiles.append(os.path.join(path, root, F))
    print("\tI found {} source files".format(len(sourceFiles)))

    return sourceFiles


def makePostScript(sourceFiles, args):
    """
    makePostScript will turn the code files into postscript files using ViM. It
    returns a list of paths to the postscript files.
    """
    postscriptFiles = []
    for F in sourceFiles:
        print(F)
        command = ["vim"]

        # Line numbering
        if args.line_numbering:
            command.append(" -c 'set nu'")
        else:
            command.append(" -c 'set nonu'")

        # Portrait vs landscape
        if args.landscape:
            command.append(" -c 'set popt+=portrait:n'")
        else:
            command.append(" -c 'set popt+=portrait:y'")

        # Make postscript
        command.append(" -c 'ha > {}.ps'".format(os.path.basename(F)))

        # Quit ViM
        command.append(" -c 'quit'")

        command.append("{}".format(F))

        print(' '.join(command))

        os.system(' '.join(command))

        postscriptFiles.append("{}.ps".format(
            os.path.abspath(os.path.basename(F))))

    return postscriptFiles


def makeLaTeXFile(path, formatter, title):
    """
    makeLateXFile will create open a file and write the appropriate LaTeX header
    information to it. It returns the file object

    path: The path to the LaTeX filename
    """
    latexFile = open(path, 'w')

    # Create the LaTeX header
    latexFile.write(textwrap.dedent(
        """
        \\documentclass[11pt]{scrartcl}
        \\usepackage{fancyvrb}
        \\usepackage[dvipsnames]{xcolor}

        \\usepackage{hyperref}
        \\hypersetup{
            backref=section,
            pdfpagelabels=true,
            colorlinks=true,
            linkcolor=RoyalBlue,
            citecolor=blue,
            urlcolor=blue,
            frenchlinks=true,
            bookmarks=true,
        }

        \title{{{title}}}
        """
    ))

    latexFile.write(formatter.get_style_defs())

    latexFile.write(textwrap.dedent(
        """

        \\begin{document}
        \\tableofcontents
        """
    ))
    return latexFile


def finishLaTeXFile(latexFile):
    """
    finishLaTeXFile will put the finishing touches on the LaTeX file and close
    it.
    """

    latexFile.write(textwrap.dedent(
        """
        \\end{document}
        """
    ))

    latexFile.close()


def makeLaTeX(sourceFiles, title):
    """
    makeLaTeX will create a LaTeX file that contains all the code found. The
    file is a random, temporary file. The path to the LaTeX file is returned

    `sourceFiles`: A list of absolute paths to files containing source code.
    """
    print("Making a LaTeX file from the source code")
    latexOptions = {"full": False,
                    "linenos": True,
                    "texcomments": False,
                    "excapeinside": True,
                    }
    formatter = pygments.formatters.get_formatter_by_name(
        "latex", **latexOptions)

    tmpDir = tempfile.mkdtemp()
    texFilename = os.path.join(tmpDir, "Code.tex")
    texFile = makeLaTeXFile(texFilename, formatter, title)

    for F in sourceFiles:
        print(F)

        latexOptions["title"] = os.path.basename(F)
        lexer = pygments.lexers.get_lexer_for_filename(F)

        texFile.write("\\pagebreak\n")
        texFile.write("\\section{{{}}}\n".format(os.path.basename(F)))
        with open(F) as codeFile:
            code = codeFile.read()
            pygments.highlight(code, lexer, formatter, outfile=texFile)

    finishLaTeXFile(texFile)

    return texFilename


if __name__ == "__main__":
    print("I'm converting Fortran into a PDF\n")

    parser = argparse.ArgumentParser(description="Convert Fortran to PDF")
    parser.add_argument('path', help="Where to search for the code")
    parser.add_argument('pdf_name', help="Path to resulting PDF.")
    parser.add_argument("--name", default=None,
                        help="Name of the code")
    parser.add_argument('--language', default="fortran",
                        help="Coding language defines preset file extensions")
    parser.add_argument("-n", "--line-numbering", default=False,
                        action="store_true",
                        help="Make PDF have line numbers")
    parser.add_argument("--landscape", default=False, action="store_true",
                        help="Make PDF in landscape mode")

    args = parser.parse_args()

    # Assume a name if one wasn't specified
    if args.name == None:
        par, name = os.path.split(args.path)
        args.name = name

    extensions = []
    if args.language == "fortran":
        print("Looking for fortran code")
        extensions = [".f", ".f90"]
    elif args.language == "python":
        extensions = [".py"]
    elif args.language == "c++":
        extensions = [".c", ".h", ".cpp", ".hpp"]
    else:
        raise NameError(
            "I don't know how to deal with {} code".format(args.language))

    sourceFiles = findSourceFiles(args.path, extensions)
    texFilename = makeLaTeX(sourceFiles, title=args.name)

    texPath = texFilename
    pdfPath = os.path.abspath(args.pdf_name)

    texDir, texFilename = os.path.split(texPath)
    texName, texExtension = texFilename.split('.')
    pdfDir = os.path.split(pdfPath)[0]

    curDir = os.getcwd()
    # Compile LaTeX
    print(texPath)
    os.chdir(texDir)
    proc = subprocess.Popen(['latexmk', texPath, '-pdf',
                             '-outdir={}'.format(pdfDir)])
    proc.communicate()

    # Copy the PDF if the compilation worked
    if not proc.returncode:
        shutil.move("{}.pdf".format(os.path.join(texDir, texName)), pdfPath)
#       shutil.rmtree(texPath)

    os.chdir(curDir)
