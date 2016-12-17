# -*- tab-width: 4
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Table, DateTime, Binary
#from sqlalchemy.types import 
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

wordurl_table = Table('wordurl', Base.metadata, Column('word_id', Integer, ForeignKey('word.id')), Column('url_id', Integer, ForeignKey('url.id'))
)

meaninggroupmeaning_table = Table('meaninggroupmeaning', Base.metadata, Column('meaninggroup_id', Integer, ForeignKey('meaninggroup.id')), Column('meaning_id', Integer, ForeignKey('meaning.id')))

class Word(Base):
    __tablename__ = 'word'

    id = Column(Integer, primary_key=True)
    # change to enum or relationship once we figure it out
    language = Column(Integer, ForeignKey('language.id'))

    # how the word is "written" or represented in abstract characters
    representation = Column(String)

    ipa_pronunciation = Column(String)
    
    # word "Kind"
    kind_id = Column(Integer, ForeignKey('wordkind.id'))
    kind = relationship("WordKind", back_populates="words")

    usages = relationship("Usage", back_populates="word")

    urls = relationship("Url", secondary=wordurl_table)

    def __repr__(self):
        return 'Word<' + repr(self.representation) + ';' + repr(self.kind) + '>'

    def __json__(self):
        return dict(kind = self.kind, ipa_pronunciation = self.ipa_pronunciation, urls = self.urls, usages = self.usages, representation = self.representation )


class Url(Base):
    __tablename__ = 'url'
    id = Column(Integer, primary_key=True)
    urlvalue = Column(String)

class UrlRequest(Base):
    __tablename__ = 'urlrequest'
    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('url.id'))
    url = relationship("Url")

    request_datetime = Column(DateTime)
    md5hash = Column(Binary)
    content_type = Column(String)
    content = Column(Binary)

class Usage(Base):
    __tablename__ = 'usage'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    desc = Column(String)
    word_id = Column(Integer, ForeignKey('word.id'))

    word = relationship("Word", back_populates="usages")

    meanings = relationship("Meaning", back_populates="usage")
    
    def __repr__(self):
        return 'Usage<' + repr(self.word) + ';' + repr(self.desc) + '>'
    def __json__(self):
        return dict(meanings = self.meanings, desc = self.desc, id = self.id)

class Meaning(Base):
    __tablename__ = 'meaning'
    id = Column(Integer, primary_key=True)

    language_id = Column(Integer, ForeignKey('language.id'))

    usage_id = Column(Integer, ForeignKey('usage.id'))
    usage = relationship("Usage", back_populates="meanings")

    ordinal = Column(Integer)
    representation = Column(String)

    groups = relationship("MeaningGroup", secondary=meaninggroupmeaning_table)

    def __repr__(self):
        return 'Meaning<' + repr(self.usage) + ';' + repr(self.representation) + '>'

class Language(Base):
    __tablename__ = 'language'
    id = Column(Integer, primary_key=True)

    name = Column(String)
    #    family_id = Column(Integer, ForeignKey('langfamily.id'))

# for now stick with one language family for simplicity
#class LanguageFamily(Base):
#    __tablename__ = 'langfamily'
#    id = Column(Integer, primary_key=True)

#    name = Column(String)
    
class WordKind(Base):
    __tablename__ = 'wordkind'
    id = Column(Integer, primary_key=True)

    name = Column(String)
    desc = Column(String)
    abbr = Column(String)
    notes = Column(String)

    words = relationship("Word", back_populates="kind")
    def __repr__(self):
        return 'WordKind<' + repr(self.name) + ';' + repr(self.abbr) + '>'

    def __json__(self):
        return dict(id = self.id, abbr = self.abbr, name = self.name)

class MeaningGroup(Base):
    __tablename__ = 'meaninggroup'
    id = Column(Integer, primary_key=True)

    name = Column(String)
    desc = Column(String)
    notes = Column(String)

    meanings = relationship("Meaning", secondary=meaninggroupmeaning_table)

class Deck(Base):
    __tablename__ = 'deck'
    id = Column(Integer, primary_key=True)
    
