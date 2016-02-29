
import argparse
import os
import shutil
import subprocess
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


def makeLaTeXFile(path, formatter, doc_options):
    """
    makeLateXFile will create open a file and write the appropriate LaTeX header
    information to it. It returns the file object

    `path`: The path to the LaTeX filename
    `formatter`: The formatter of the soruce code
    `doc_options`: The options for the document
    """
    latexFile = open(path, 'w')

    # Create the LaTeX header
    if doc_options["landscape"]:
        latexFile.write("\\documentclass[11pt, landscape]{scrartcl}")
    else:
        latexFile.write("\\documentclass[11pt]{scrartcl}")
    latexFile.write(textwrap.dedent(
        """
        \\usepackage{{fancyvrb}}
        \\usepackage[dvipsnames]{{xcolor}}

        \\usepackage{{hyperref}}
        \\hypersetup{{
            backref=section,
            pdfpagelabels=true,
            colorlinks=true,
            linkcolor=RoyalBlue,
            citecolor=blue,
            urlcolor=blue,
            frenchlinks=true,
            bookmarks=true,
        }}

        \\title{{{title}}}
        \\author{{{author}}}
        """.format(**doc_options)
    ))

    latexFile.write(formatter.get_style_defs())

    latexFile.write(textwrap.dedent(
        """

        \\begin{document}
        \\maketitle
        \\pagebreak
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


def makeLaTeX(sourceFiles, title, author, landscape):
    """
    makeLaTeX will create a LaTeX file that contains all the code found. The
    file is a random, temporary file. The path to the LaTeX file is returned

    `sourceFiles`: A list of absolute paths to files containing source code.
    `title`: The title and name of the document
    `author`: The author of the source code
    `landscale`: Whether or
    """
    print("Making a LaTeX file from the source code")
    latexOptions = {"full": False,
                    "linenos": True,
                    "texcomments": False,
                    "excapeinside": True,
                    }
    formatter = pygments.formatters.get_formatter_by_name(
        "latex", **latexOptions)

    texFilename = "{}.tex".format(title)
    doc_options = {"title": title,
                   "author": author,
                   "landscape": landscape
                   }
    texFile = makeLaTeXFile(texFilename, formatter, doc_options)

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
    parser.add_argument("name", default=None,
                        help="Name of the code")
    parser.add_argument('--language', default="fortran",
                        help="Coding language defines preset file extensions")
    parser.add_argument("-n", "--line-numbering", default=False,
                        action="store_true",
                        help="Make PDF have line numbers")
    parser.add_argument("--landscape", default=False, action="store_true",
                        help="Make PDF in landscape mode")
    parser.add_argument("--author", default="\\texttt{code2PDF.py}",
                        help="The author of the source code.")

    args = parser.parse_args()

    extensions = []
    if args.language.lower() == "fortran":
        print("Looking for fortran code")
        extensions = [".f", ".f90"]
    elif args.language.lower() == "python":
        extensions = [".py"]
    elif args.language.lower() == "c++":
        extensions = [".c", ".h", ".cpp", ".hpp"]
    else:
        raise NameError(
            "I don't know how to deal with {} code".format(args.language))

    sourceFiles = findSourceFiles(args.path, extensions)
    texFilename = makeLaTeX(sourceFiles[:3],
                            title=args.name,
                            author=args.author,
                            landscape=args.landscape
                            )

    texPath = texFilename

    texDir, texFilename = os.path.split(texPath)
    texName, texExtension = texFilename.split('.')

    # Compile LaTeX
    proc = subprocess.Popen(['latexmk', texPath, '-pdf'])
    proc.communicate()

