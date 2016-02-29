
import argparse
import os
import re
import subprocess
import textwrap

import PyPDF2
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
                if F.lower().endswith(ext):
                    sourceFiles.append(os.path.join(path, root, F))

    print("Found {} source code files".format(len(sourceFiles)))
    return sourceFiles


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
        \\subtitle{{PDF generated by \href{{https://github.com/jlconlin/code2PDF}}{{code2PDF.py}}}}
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


def makeLaTeX(sourceFiles, title, author, landscape, lineNumbering):
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
                    "linenos": lineNumbering,
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

        latexOptions["title"] = os.path.basename(F)
        lexer = pygments.lexers.get_lexer_for_filename(F)

        texFile.write("\\pagebreak\n")
        filename = os.path.basename(F)
        filename = filename.replace("_", "\_")
        texFile.write("\\section{{{}}}\n".format(filename))
        with open(F) as codeFile:
            code = codeFile.read()
            pygments.highlight(code, lexer, formatter, outfile=texFile)

    finishLaTeXFile(texFile)

    return texFilename


def compileLaTeX(texPath):
    """
    compileLaTeX will compile the LaTeX document. It returns the absolute path
    to the generated PDF.

    `texPath`: Absoulate path to LaTeX file.
    """
    # Compile LaTeX
    proc = subprocess.Popen(['latexmk', texPath, '-pdf'])
    proc.communicate()

    name, ext = os.path.splitext(texPath)

    return name+".pdf"


def _setup_page_id_to_num(pdf, pages=None, _result=None, _num_pages=None):
    """
    Create a map of page IDs to numerical page numbers. Stolen from
        http://stackoverflow.com/questions/8329748/how-to-get-bookmarks-page-number
    """
    if _result is None:
        _result = {}
    if pages is None:
        _num_pages = []
        pages = pdf.trailer["/Root"].getObject()["/Pages"].getObject()
    t = pages["/Type"]
    if t == "/Pages":
        for page in pages["/Kids"]:
            _result[page.idnum] = len(_num_pages)
            _setup_page_id_to_num(pdf, page.getObject(), _result, _num_pages)
    elif t == "/Page":
        _num_pages.append(1)
    return _result


def findRoutines(regex):
    """
    findRoutines will return a list of tuples containing the name of a
    subroutine and the page number on which that subroutine is found.

    `regex`: regular expression describing the method for finding the
        subroutine. This must use named capture groups with one group called
        'name' indicating the name of the subroutine.
    """
    print("Searching PDF for subroutines")
    routines = []
    for pageNum in range(PDF.getNumPages()):
        content = PDF.getPage(pageNum).extractText()
        found = regex.finditer(content)
        for sub_r in found:
            routines.append((sub_r.groupdict()['name'], pageNum))

    return routines


def addRoutineBookmarks(bookmarks, routines, outPDF):
    """
    addRoutineBookmarks will add PDF bookmarks based on the found routines.

    `bookmarks`: Parent bookmarks from PDF without bookmarks for routines
    `routines`: List of tuples containing routine names and PDF page numbers
    `outPDF`: The new PDF file being created
    """
    for i in range(len(bookmarks)):
        BM = bookmarks[i]
        pn_current = bookmark_map[BM.page.idnum]
        try:
            pn_next = bookmark_map[bookmarks[i+1].page.idnum]
        except IndexError:
            pn_next = 1E6

        newBM = outPDF.addBookmark(BM["/Title"], pn_current, parent=None)

        # Iterate over all the found routines
        for r in routines:

            # Only store those bookmarks tht are the current children
            if (r[1] >= pn_current):
                if (r[1] < pn_next):
                    outPDF.addBookmark(r[0], r[1], parent=newBM)
                else:
                    break


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
    else:
        raise NameError(
            "I don't know how to deal with {} code".format(args.language))

    sourceFiles = findSourceFiles(args.path, extensions)
    texFilename = makeLaTeX(sourceFiles,
                            title=args.name,
                            author=args.author,
                            landscape=args.landscape,
                            lineNumbering=args.line_numbering
                            )
    PDFfile = compileLaTeX(texFilename)

    PDF = PyPDF2.PdfFileReader(PDFfile)
    bookmarks = PDF.getOutlines()
    bookmark_map = _setup_page_id_to_num(PDF)

    BMs = [(B, bookmark_map[B.page.idnum]) for B in bookmarks]

    subroutine_re = re.compile(
        """
        (?<!end\s)                      # Don't match the end of subroutine/func
        (subroutine|function)\s+        # Indication of subroutine/function
        (?P<name>\w+)                   # Name of subroutine/function
        """, re.MULTILINE | re.VERBOSE)
    routines = findRoutines(subroutine_re)

    outPDF = PyPDF2.PdfFileWriter()
    outPDF.appendPagesFromReader(PDF)
    addRoutineBookmarks(bookmarks, routines, outPDF)

    # Write new PDF file
    outPDFStream = open("{}.pdf".format(args.name), 'wb')
    outPDF.write(outPDFStream)
    outPDFStream.close()
