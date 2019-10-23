# Check Arxiv

This script is developed to allow the user to obtain a pdf summarizing the new arXiv articles for a given day.
It will create two folders: one to store the pdf files, and one to store the tex files.

## Requirements
This code has a few external dependencies:
1. [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
2. [pylatex](https://jeltef.github.io/PyLaTeX/current/)
3. [pyyaml](https://github.com/yaml/pyyaml)

## Setup
In order to run the code, the user will have to modify the configuration file. There are only two settings that need
to be set, subjects and path. The subjects are the different subjects from the arXiv to be checked, and the
path is the location to store the results. Below is an example:

```yaml
subjects:
    - hep-ph
    - hep-ex
    - hep-lat
    - hep-th
    - cs.LG
    - stat.ML

path:
    /home/isaacson/Documents/ArXiv
```
