from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

class Word(Base):
    __tablename__ = 'word'

    id = Column(Integer, primary_key=True)
    # change to enum or relationship once we figure it out
    language = Column(Integer, ForeignKey('language.id'))

    # how the word is "written" or represented in abstract characters
    representation = Column(String)
    
    # word "Kind"
    kind_id = Column(Integer, ForeignKey('wordkind.id'))
    kind = relationship("WordKind", back_populates="words")

    usages = relationship("Usage")

class Usage(Base):
    __tablename__ = 'usage'
    
    id = Column(Integer, primary_key=True)
    desc = Column(String)
    word_id = Column(Integer, ForeignKey('word.id'))

    meanings = relationship("Meaning")

class Meaning(Base):
    __tablename__ = 'meaning'
    id = Column(Integer, primary_key=True)

    language_id = Column(Integer, ForeignKey('language.id'))
    usage_id = Column(Integer, ForeignKey('usage.id'))
    ordinal = Column(Integer)
    representation = Column(String)

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
