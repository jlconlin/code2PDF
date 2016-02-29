# code2PDF
Create a static PDF of your code.

This project requires the following Pythong libraries to be installed 
(in addition to the standard Python libraries).

 - [pygments](http://pygments.org)
 - [PyPDF](https://github.com/mstamy2/PyPDF2)
 - latexmk and LaTeX compiler (preferably [TeXLIve](http://www.tug.org/texlive)

## Installation
No installation is needed just run it.

## Running

```
usage: code2PDF.py [-h] [--language LANGUAGE] [-n] [--landscape]
                   [--author AUTHOR]
                   path name

Convert Fortran to PDF

positional arguments:
  path                  Where to search for the code
  name                  Name of the code

optional arguments:
  -h, --help            show this help message and exit
  --language LANGUAGE   Coding language defines preset file extensions
  -n, --line-numbering  Make PDF have line numbers
  --landscape           Make PDF in landscape mode
  --author AUTHOR       The author of the source code.
```

**Note:** This can take several minutes to run for about 100k lines of source
code.
