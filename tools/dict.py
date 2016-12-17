#!/usr/bin/python -*- tab-width: 4
#
# Author: Kay McCormick
# Purpose: process definition list HTML into entities backed by datastore
# Notes:
#  This is a mix of BeautifulSoup and direct lxml which makes for a
#  messy business.
#  Parsing is nearly but not fully complete.

from uuid import uuid4
import hashlib
import datetime
import base64
import heptet.dict.datamodel.words as w
from copy import deepcopy,copy
from lxml.builder import E
#import dict_lib

import requests
import collections
import sys
import codecs
import os
import logging
from bs4 import BeautifulSoup
from bs4 import UnicodeDammit
import bs4
import lxml.html
from lxml import etree
#from lxml.html.soupparser import fromstring
import inspect
import argparse
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

password = '';
logger = logging.getLogger(__name__)
engine = create_engine('postgresql://sqlalchemy:' + password + '@localhost/sqlalchemy', echo=False)

generateXml = False

# xml Log is different from generateXml

def extract_text(elem, strContent, skipWhitespace = True, trimWhitespace = True):
    logging.log(5, "entering extract_text")
    if elem == None:
        logging.warn("extract_text called with None!")
        return

    logging.debug("e: %s", etree.tostring(elem))

    if elem.text != None:
        logging.debug("T: %s", elem.text)
        strContent.append(copy(elem.text))
    
    for child in elem.iterchildren():
        extract_text(child, strContent, skipWhitespace, trimWhitespace)
        if child.tail != None:
            logging.debug("Tail = %s", child.tail)
            strContent.append(copy(child.tail))
    
    logging.debug("strContent = %s", strContent)
    logging.log(5, "leaving extrac_text")

    return

    if isinstance(elem, lxml.html.HtmlElement):
        iterable = elem.iterchildren()
    else:
        iterable = elem

    for dataElem in iterable:
        logging.debug("extract_text: processing %s", dataElem)
        if isinstance(dataElem, lxml.html.HtmlElement):
            logging.debug("tag %s", dataElem.tag)
            logging.debug("taclass = %s", dataElem.get("class"))
            zclass = []
            if dataElem.get("class") != None:
                 zclass = dataElem.get("class").split(' ')
            if len(zclass) > 0:
                logging.debug("class %s", zclass)

                ## checking for conjugate doesnt work because its
                ## a child of strong, boo

                ## skip over this class completely
                if "conjugate" in zclass:
                    continue

                ## for this class we wish to elide child "span" elements
                if "tooltip" in zclass:
                    #logging.debug(u"test: %s [%s]", str(x), type(x).__name__) or 
                    ##fix
                    extract_text(filter(lambda x:
                                        (isinstance(x, bs4.element.NavigableString) or
                                         x.tag != "span"), dataElem.iterchildren()),
                                 strContent, skipWhitespace)
                    continue

            extract_text(dataElem, strContent, skipWhitespace)
        else:
            assert false
            #for xxx in dataElem.strings:
            #    strContent.append(xxx)
            if skipWhitespace and dataElem.text.isspace():
                pass
            else:
                if trimWhitespace:
                    dataElem = dataElem.strip()
                
                logging.debug("appending {%s}", dataElem)
                strContent.append(dataElem)

    logging.log(5, "leaving extract_text")


def load_abbrs_to_memory():
    # path elsewhere in perforce depot - must be updated
    abbrsFile = codecs.open("../../../scripts/dict-refactor/abbrev.html", "r", "utf-8")
    contents = abbrsFile.read()
    abbrsFile.close()
    soup = BeautifulSoup(contents, "lxml")
    table = soup.find("table", class_ = "wrd main")
    rows = table.tbody.findAll("tr")

    #logging.debug("%s", rows[2:])
    abbrDict = {}
    for row in rows[2:]:
        tds = row.findAll("td")
        if(len(tds) == 3):
            english = tds[0].string
            abbr = tds[1].string
            french = tds[2].string
            if french == None or len(french) == 0 or french.isspace():
                french = english

        if abbr == "\xa0":
            break
            
        #        logging.debug("%s %s", , french)
        for anabbr in abbr.split("/"):
            abbrDict[anabbr] = french
            
        else:
            logging.debug("%s", tds)
            
    return abbrDict

def CLASS(*args): # class is a reserved word in Python
     return {"class":' '.join(args)}

div1 = E.div()
div2 = E.div(CLASS("msgs"))
body = E.body(div1, div2)

html = page = (
    E.html(
        E.head(
            E.link(rel="stylesheet", href="log.css"),
            E.title("HTML Log")
            ),
        body
        )
    )

xmlLog = body
xmlLogTree = etree.ElementTree(html)

class XmlLogHandler(logging.Handler):
    def __init__(self, div):
        super(XmlLogHandler, self).__init__()
        self.div = div
        self.posElem = None
    def emit(self, record):
        msg = self.format(record)
        id = ""
        if self.posElem != None:
            if "id" in self.posElem:
                id = self.posElem["id"]
            else:
                id = str(uuid4())
                self.posElem.set("id", id)

#            etree.SubElement(self.posElem, "img")
        self.div.append(E.p(E.span(id, CLASS("ref")), msg))

h = XmlLogHandler(div2)
logger.addHandler(h)

class DictTool:
    def __init__(self, session):
        self.curWordObj = None
        self.session = session
        self.ipaPron = None

        pass

    def processFirstCell(self, cell):
        h.posElem = cell
        logger.debug("processFirstCell: %s", etree.tostring(cell))
        if len(cell) == 0 and (cell.text == None or cell.text.isspace()):
            # empty, do nothing
            #pass
            return False
        else:
            if len(cell.getchildren()) == 0:
                logger.info("%s", cell.text)
            classes = {}
            class_ = cell.get("class")
            if class_ != None:
                classes = class_.split(' ')

            strongText = cell.xpath("strong/text()")
            kind = cell.xpath("em/text()") #[contains(@class, 'tooltip')]
            assert len(kind) <= 1
            logger.debug("kind=%s", kind)
            # assert len(strongText) <= 1,
            #  "strongText length is %d" % len(strongText)
            if len(strongText) > 0:
                j = ''.join(strongText)
                logger.debug("t=%s",  j)
                # use constant FIXME
                if "FrWrd" in classes:

                    ## xml junk
                    if generateXml:
                        curWordElem = etree.SubElement(curElem, "word")
                        curWordElem.set('lang', 'fr')
                        curWordElem.set('value', j)

                    ## look up the "word kind"
                    candKind = None
                    if len(kind) > 0:
                        if kind[0] not in abbrObjDict:
                            logger.error("no word kind found for %s", kind[0])
                        else:
                            ## error
                            candKind = abbrObjDict[kind[0]]
                            if generateXml:
                                curWordElem.set('kind', kind[0])
                    else:
                        logger.error("no word kind for %s", word)

                    # find model obj
                    candWord = self.session.query(w.Word).filter_by(representation = j, kind = candKind).one_or_none()
                    if candWord == None:
                        myspan = E.span("create")
                        logger.debug("%s", etree.tostring(cell))
                        logger.debug("appending %s", etree.tostring(myspan))
                        etree.SubElement(cell, "span").text="\u2756"
                        logger.debug("%s", etree.tostring(cell))
                        candWord = w.Word(representation = j, kind = candKind, ipa_pronunciation = self.ipaPron)
                        candWord.urls.append(self.curUrl)
                        self.session.add(candWord)

                    self.curWordObj = candWord
        return True


parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true")
parser.add_argument("--fine", action="store_true")
parser.add_argument("--info", action="store_true")
parser.add_argument("--create-schema", action="store_true")
parser.add_argument("--load-abbrs", action="store_true")
args = parser.parse_args()

if args.debug:
    logging.basicConfig(level=5)
else:
    logging.basicConfig(level=logging.INFO)

logger.debug("Encoding for stdout: %s", sys.stdout.encoding)

Session = sessionmaker(bind=engine)
session = Session()
dictTool = DictTool(session)

if args.create_schema:
    logger.debug("Creating schema...")
    w.Base.metadata.create_all(engine)
    lang = w.Language(name="French")
    session.add(lang)
    wordkind = w.WordKind(name="Default")
    session.add(wordkind)
    session.commit()

if args.load_abbrs:
    # bug here - "prep" shows up twice, once with a french abbreviation
    abbrDict = load_abbrs_to_memory()
    for k in abbrDict:
        kind = w.WordKind(name = abbrDict[k], abbr = k, desc = abbrDict[k])
        session.add(kind)
    session.commit()

abbrObjDict = {}
for instance in session.query(w.WordKind):
    abbrObjDict[instance.abbr] = instance

if args.debug:
    logger.debug("Printing information and exiting.")
    logger.debug("len(abbrObjDict) = %d", len(abbrObjDict))
    logger.debug("%s", repr(w.Word.__table__))
    quit()

def lineno():
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno

rootXmlElem = etree.Element('dictionary')
parser = "lxml"

#logger._defaultFormatter = logger.Formatter(u"%(message)s")

meaningGroup = w.MeaningGroup(name = "Marked for Inclusion", desc = "Marked for Inclusion")
session.add(meaningGroup)
                
path = "..\..\..\scripts\dict-refactor\defs"
md5o = hashlib.md5()
for defFilename in os.listdir(path):
#for defFilename in ["atteler"]:
    word = defFilename

#    url = "file:///d:/depot/scripts/dict-refactor/defs/" + defFilename
    url = "http://www.wordreference.com/fren/" + defFilename

    candUrlO = session.query(w.Url).filter_by(urlvalue = url).one_or_none()
    if candUrlO == None:
        urlo = w.Url(urlvalue = url)
        session.add(urlo)
    else:
        urlo = candUrlO

    dictTool.curUrl = urlo

    if makeRequest:
        urlReq = w.UrlRequest(url = urlo)
        session.add(urlReq)
        
        r = requests.get(url)
        clen = int(r.headers["content-length"])
        logger.info("%d", clen)
    
        content = r.content

        root = lxml.html.fromstring(content)
        ads = root.xpath("//td[@id='adrighttop' or @id='adrightbottom']")
        for ad in ads:
            ad.getparent().remove(ad)
            ads = root.xpath("//table[contains(@class, 'rightcolumn')]")
        
        for ad in ads:
            ad.getparent().remove(ad)
                
        newcontent = etree.tostring(root)
        outc = open("out-current.txt", "wb")
        outc.write(newcontent)
        outc.close()

        md5o.update(newcontent)
        logging.info("%s", md5o.digest())
        urlReq.md5hash = md5o.digest()
        urlReq.request_datetime = datetime.datetime.now()
        urlReq.content_type = r.headers["content-type"]
        urlReq.content = content

    table = E.table(E.caption(word))
    body.append(table)

    ## Announce our intentions
    logger.warn("processing %s", word)

    ## Open our input file
    defFile = codecs.open(os.path.join(path, str(defFilename)), "r", "utf-8")
    contents = defFile.read()
    defFile.close()

    ## XML Generation
    dictEntryElem = etree.Element('dictionary-entry')
    dictEntryElem.set('value', word)
    curElem = dictEntryElem

    root = lxml.html.fromstring(contents)

    h3 = root.xpath("//h3[contains(@class, 'headerWord')]")
    if len(h3) == 0:
        logging.warn("no h3 header, skipping")
        continue
    assert len(h3) == 1
    headerWord = h3[0].text
    assert headerWord != None
    logging.warn("headerWord = %s", headerWord)

    pron = root.xpath("//span[@id='pronWR']")
    assert len(pron) <= 1
    if len(pron) == 1:
        pronText = pron[0].text
        pronText = pronText[1:len(pronText) - 1]
        logger.warn("pronunciation: %s", pronText)
        dictTool.ipaPron = pronText
    else:
        dictTool.ipaPron = None

    rows = root.xpath("//table[@class='WRD'][1]/tr/td[@title='Principal Translations']/../../tr[td[1][not(@colspan)]][td[2][not(@colspan)]]")

    logger.debug("xpath got %d elems", len(rows))
    curWordElem = None
    for row in rows:
        logger.debug("processing row...")
#        logger.debug("firstCell = %s", etree.tostring(firstCell))
        
#        row = firstCell.getparent()
        logger.debug("row = %s", etree.tostring(row))

        cell = row[0]
        if dictTool.processFirstCell(cell):
            logging.debug("clearing curUsageObj")
            curUsageObj = None
                        
        cell = row[1]
#        dictTool.processSecondCell(cell)

        logger.debug("cell2 = %s", etree.tostring(cell))
                        
        txt = ""
        x = cell.xpath("i[1]/text()[1]")
        assert len(x) == 0 or len(x) == 1
        if len(x) == 1:
            logger.debug("x = %s", repr(x))
            logger.debug("cell = %s", etree.tostring(cell))
            p = x[0].getparent() # i tag
            if p.getprevious() == None:
                if p.getparent().text == None:
                    p.getparent().text = copy(p.tail)
                else:
                    logger.debug("p = %s", etree.tostring(p))
                    logger.debug("pp = %s", etree.tostring(p.getparent()))
                    cell.text += p.tail
            else:
                if p.getprevious().text == None:
                    p.getprevious().text = copy(p.tail)
                else:
                    p.getprevious().text += p.tail
            x[0].getparent().getparent().remove(x[0].getparent())

            logger.debug("cell = %s", etree.tostring(cell))

            
        
        if cell.text != None and not cell.text.isspace(): # not sure if this is the right condition

            logger.debug("creating element wordEntry")

            if generateXml:
                wordEntryElem = etree.SubElement(curWordElem, "word-entry")
                senseElem = etree.SubElement(wordEntryElem, "sense")

            txt = cell.text.strip()
            
            if len(cell) > 0:
                child = cell[0]
                if child.tag == "i":
                    misc = child.text.strip()
                    logger.debug("misc = %s", misc)
                    txt = child.tail.strip()
                elif child.tag == "span":
                    spanClass = child.get("class")
                    assert spanClass == "dsense"
                    dsense = child.xpath("descendant::text()")
                    if generateXml:
                        senseElem.set("dsense", ''.join(dsense))
                else:
                    assert False, "unrecognized tag in column 2: %s" % etree.tostring(child)
            logger.debug("txt = %s", txt)
            ## we don't want to create a usage if one exists!
            curUsageObj = session.query(w.Usage).filter_by(word = dictTool.curWordObj, name = txt).one_or_none()
            if curUsageObj == None:
                 curUsageObj = w.Usage()
                 curUsageObj.desc = txt
                 curUsageObj.name = txt
                 session.add(curUsageObj)

            if generateXml:
                senseElem.text = txt

            # ERROR
            assert dictTool.curWordObj != None
            dictTool.curWordObj.usages.append(curUsageObj)
#            curUsageObj.word_id = curWordObj.id

#            session.commit()

        cell = row[2]
        kind = cell.xpath("em/text()")
        assert len(kind) <= 1
        logger.debug("kind=%s", kind)
        if len(kind) > 0:
            kind[0].getparent().getparent().remove(kind[0].getparent())

        logger.debug("cell3 = %s", etree.tostring(cell))
        classes = {}
        class_ = cell.get("class")
        if class_ != None:
            classes = class_.split(' ')

        if "ToWrd" in classes:
            # assert toWordElem.text != None
            if cell.text != None:
                if generateXml:
                     toWordElem = etree.SubElement(wordEntryElem, "to-word")
                     toWordElem.text = cell.text.strip()

                strContent = collections.deque()
                extract_text(cell, strContent)
                # check for existence
                rep = ''.join(strContent)
                cand = session.query(w.Meaning).filter_by(language_id = 1, usage = curUsageObj, representation = rep).one_or_none()
                if cand != None:
                    logging.debug("cand = %s", repr(cand))
                else:
                    curMeaningObj = w.Meaning(language_id = 1,
                                              usage = curUsageObj,
                                              representation = rep)
                    curMeaningObj.groups.append(meaningGroup)
                    logging.debug("creating meaning = %s", repr(curMeaningObj))
                    session.add(curMeaningObj)

        logger.debug("appending: %s", etree.tostring(row))
        table.append(deepcopy(row))

    
    if generateXml:
        rootXmlElem.append(dictEntryElem)

#    break
    continue
    soup = BeautifulSoup(contents, parser)
    title = soup.title
#    print title.string
    if title.string == "Object moved":
#        print "hi"
        continue

    td = soup.find(whatIwant)
    if soup.find("p", id='noEntryFound') != None:
        logger.warning("found 'noEntryFound' tag for %s", word);
        if td != None:
            logger.error("anomalous condition - also translations!")

        continue

    if td == None:
        logger.error("cant find translations for %s", word)
        next

    parent = td.parent
    if parent == None:
        logger.error("gak")

        # this table also has class "WRD" - might that work?
    row = td.parent
    table =  td.parent.parent
    #print table.prettify()

#    print row.name
    rowId = None
    while row.next_sibling != None:
        row = row.next_sibling
        #        repr(type(row)))

        if isinstance(row, bs4.element.NavigableString):
            if(row.isspace() or len(row) == 0):
                continue
            else:
                logger.warning("Non-empty string at same level as table rows.")
                logger.debug(logUnicodeString(logger.DEBUG, row.string))
            continue
        
        if not isinstance(row, bs4.element.Tag):
            logger.warn("not a tag %s", type(row))
            continue

        logger.debug("processing row %s", row)

        firstColumn = row.contents[0]
        logger.debug("%s", firstColumn)

        i = 0
        for tableData in row.children:
            strContent = collections.deque()
            classDict = {}
            classStr = " "
            if tableData.has_attr('class'):
                for cl in tableData["class"]:
                    classDict[cl] = True

                classStr += ' '.join(tableData["class"])

            extract_text(tableData, strContent, skipWhitespace = True)
            if len(strContent) > 0:
                if "FrWrd" in classDict:
                    curWordElem = etree.Element('word')
                    curWordElem.set('lang', 'fr')
                    logger.debug("frword: %s", strContent)
                    curWordElem.set('value', strContent.popleft())
                    curElem.append(curWordElem)
                    
                logger.debug("%d col%d%s %s {%s}", lineno(), i,
                             classStr, strContent, tableData)

                if i == 1 and "FrEx" not in classDict and "ToEx" not in classDict:
                    logger.debug("woop %s", strContent)

                for ss in strContent:
                    if ss in abbrDict: 
                        logger.debug("found abbr %s [%s]", ss, abbrDict[ss])
                        curWordElem.set('kind', abbrDict[ss])
                    elif False:
                        e = etree.Element("data")
                        e.text = str(ss)
                        curElem.append(e)

            i += 1

        
        
        if not row.has_attr('id'):
            logger.warning("no id attr on row")
        else:
            rowId = row['id']

        logger.debug("%s %s", row['class'], rowId)
        
    x=table.find("td", class_='FrWrd')
    x=x.contents[0]
#    print defFilename + "\t" + str(x)
    rootXmlElem.append(dictEntryElem)
    break

    
#for table in soup.find_all('table'):
#    print str(table.get('id')) + "\t" + str(table.get("class"))
#    for tr in table.find_all('tr'):
#        print "TR" + str(table.get("class"))
        
#f.write(table.prettify())

session.commit()

if generateXml:
    xmlOutputStream = open("output.xml", "wb")
    xmlOutputStream.write(etree.tostring(rootXmlElem, encoding="UTF-8"))
    xmlOutputStream.close()

xmlLogTree.write("log.html", pretty_print = True)

