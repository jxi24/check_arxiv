#!/usr/bin/env python
""" Python script to get new articles from the arxiv. """

import time
import datetime
import os
import subprocess
import glob

from urllib.request import urlopen
from bs4 import BeautifulSoup
from pylatex.base_classes import CommandBase, Arguments
from pylatex.package import Package
from pylatex import Document, Section, Command, Itemize, Math
from pylatex.utils import NoEscape, bold

import notify

import yaml

LOC, FILE = os.path.split(__file__)

with open(os.path.join(LOC, 'config.yaml'), 'r') as config_file:
    try:
        config = yaml.safe_load(config_file)
    except yaml.YAMLError as exc:
        print(exc)

SUBJECTS = config['subjects']

PATH = config['path']


class URLCommand(CommandBase):
    """ Allow urls to be added to latex. """
    _latex_name = 'url'
    packages = [Package('hyperref')]


class Article:
    """ Class to hold information about articles. """
    def __init__(self, title, authors, abstract, url):
        self.title = title
        self.authors = authors
        self.abstract = abstract.replace('\n', ' ')
        self.url = url

    def __str__(self):
        return 'Title: {}\nAuthors: {}\nAbstract: {}\nLink: {}\n'.format(
            self.title, self.authors, self.abstract, self.url)

    def latex(self, doc):
        """ Add article to latex document. """

        doc.append(bold('Title: '))
        title = self.title.split('$')
        title_text = title[::2]
        title_math = title[1::2]
        for i, _ in enumerate(title_text):
            doc.append(NoEscape('{}'.format(title_text[i])))
            if i != len(title_text) - 1:
                math = Math(data=[r'{}'.format(title_math[i])],
                            inline=True, escape=False)
                doc.append(math)
            else:
                doc.append(NoEscape('\n'))

        doc.append(bold('Authors: '))
        doc.append('{}\n'.format(self.authors))

        doc.append(bold('Abstract: '))
        abstract = self.abstract.split('$')
        abstract_text = abstract[::2]
        abstract_math = abstract[1::2]
        for i, _ in enumerate(abstract_text):
            doc.append(abstract_text[i])
            if i != len(abstract_text) - 1:
                math = Math(data=[r'{}'.format(abstract_math[i])],
                            inline=True, escape=False)
                doc.append(math)
                doc.append(NoEscape(r'\ '))
            else:
                doc.append(NoEscape('\n'))

        doc.append(bold('Link: '))
        doc.append(URLCommand(arguments=Arguments(self.url)))


def get_articles(subject):
    """ Use the rss feed to get the arxiv articles for a given subject. """
    articles = []

    parse_xml_url = urlopen('http://arxiv.org/rss/{}'.format(subject))
    xml_page = parse_xml_url.read()
    parse_xml_url.close()

    soup_page = BeautifulSoup(xml_page, 'xml')
    news_list = soup_page.findAll('item')

    title_string = 'SUBJECT: {}'.format(subject)
    print(title_string)
    print('-'*len(title_string), '\n')

    for getfeed in news_list:
        title = getfeed.title.text
        authors = BeautifulSoup(getfeed.creator.text,
                                features='lxml').text
        abstract = BeautifulSoup(getfeed.description.text,
                                 features='lxml').text[:-1]
        url = getfeed.link.text
        if 'UPDATED' in title:
            continue
        if subject not in title:
            continue

        article = Article(title, authors, abstract, url)
        articles.append(article)
        print(article)

    if subject != SUBJECTS[-1]:
        time.sleep(5)
    return articles


def fill_document(doc):
    """ Add the text to the latex document. """
    for subject in SUBJECTS:
        articles = get_articles(subject)
        with doc.create(Section('Subject: {}'.format(subject))):
            with doc.create(Itemize()) as itemize:
                for article in articles:
                    itemize.add_item('')
                    article.latex(itemize)


def main(pdf):
    """ Create pdf for today's arxiv. """

    # Geometry Options
    geometry_options = {
        'head': '40pt',
        'margin': '0.25in',
        'bottom': '0.5in',
        'includeheadfoot': True
    }

    # Build tex document
    doc = Document(geometry_options=geometry_options)

    doc.packages.append(Package('amssymb'))

    doc.preamble.append(Command('title', 'ArXiv Articles'))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))

    fill_document(doc)

    # Compile tex into pdf
    try:
        doc.generate_pdf(pdf, clean_tex=False)
        failed = False
    except subprocess.CalledProcessError:
        failed = True

    # Create directories if needed
    if not os.path.exists(os.path.join(PATH, 'pdfs')):
        os.makedirs(os.path.join(PATH, 'pdfs'))
    if not os.path.exists(os.path.join(PATH, 'tex')):
        os.makedirs(os.path.join(PATH, 'tex'))

    # Move files
    os.rename('{}.pdf'.format(pdf),
              os.path.join(PATH, 'pdfs', '{}.pdf'.format(pdf)))

    os.rename('{}.tex'.format(pdf),
              os.path.join(PATH, 'tex', '{}.tex'.format(pdf)))

    # Remove unneeded files if failed
    if failed:
        for filename in glob.glob('arxiv_*'):
            os.remove(filename)


def onOpen(notification, action, pdf_name):
    """Open the generated pdf.

    Args:
        notification (Notification): Notification passed in.
        action (str): Action to take, should be 'open'.

    """
    assert(action == 'open'), 'Action was not open!'
    print('Open pdf')
    pdf_name = os.path.join(PATH, 'pdfs', '{}.pdf'.format(pdf_name))
    subprocess.Popen(['zathura', pdf_name])
    notification.close()


def onClose(notification):
    """ Close notification.

    Args:
        notification (Notification): Notification to close.

    """
    app.quit()


if __name__ == '__main__':
    import sys
    from PyQt5.QtCore import QCoreApplication
    app = QCoreApplication(sys.argv)

    # Get todays date
    now = datetime.datetime.now()
    year = now.year - 2000
    month = now.month
    day = now.day

    # Create name for output pdf
    pdf = 'arxiv_{}{:02}{:02}'.format(year, month, day)

    main(pdf)
    notify.init('arxiv')

    icon_path = os.path.join(PATH, 'arxiv.png')
    notification = notify.Notification('Arxiv Notification',
                                       'The arxiv check has been completed.',
                                       timeout=30000,
                                       )
    notification.setUrgency(notify.Urgency.NORMAL)
    notification.setCategory('device')
    notification.setIconPath(icon_path)
    notification.addAction('open', 'Open', onOpen, pdf)
    notification.onClosed(onClose)
    notification.show()
    app.exec_()
