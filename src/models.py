##
## Created       : Mon May 14 23:04:44 IST 2012
## Last Modified : Fri Jun 29 23:32:30 IST 2012
##
## Copyright (C) 2012 Sriram Karra <karra.etc@gmail.com>
##
## Licensed under the GNU AGPL v3
##
#####
##
## Our database schema delcarations, and other such hair raising stuff.
##

import datetime, logging, re

from   sqlalchemy        import orm, create_engine
from   sqlalchemy.orm    import relationship, backref
from   sqlalchemy.types  import Integer, Boolean, DateTime, Text, Unicode
from   sqlalchemy.dialects.sqlite import DATE
from   sqlalchemy.schema import Column, ForeignKey, Table

from   sqlalchemy.ext.declarative import declarative_base

Base   = declarative_base()

def now():
    return datetime.datetime.now()

def today():
    """Return today's date in YYYY/MM/DD format"""
    d = datetime.date.today()
    return "%4d/%02d/%02d" % (d.year, d.month, d.day)

def today_uk():
    """Return today's date in DD/MM/YYYY format"""
    d = datetime.date.today()
    return "%4d/%02d/%02d" % (d.day, d.month, d.year)

myd = DATE(storage_format="%04d/%02d/%02d",
           regexp=re.compile("(\d+)/(\d+)/(\d+)"))

class Patient(Base):
    __tablename__ = 'patient'

    id      = Column(Integer, primary_key=True)
    title   = Column(Unicode(5))
    name    = Column(Unicode(255), nullable=False)
    regdate = Column(DateTime(), default=now)
    age     = Column(Integer, nullable=False)
    gender  = Column(Unicode(6), nullable=False)

    phone   = Column(Unicode(255), nullable=False)
    address = Column(Text())

    relative          = Column(Unicode(255))
    relative_phone    = Column(Unicode(255))
    relative_relation = Column(Unicode(255))

    occupation = Column(Unicode(255))

    free    = Column(Boolean, default=True)
    reg_fee = Column(Integer, default=0)

    consultations = relationship("Consultation", 
                                 backref=backref('patient',
                                                 cascade="all"))

    def __repr__(self):
        return ("<Patient(id:%d,Name:%s, age:%d)>" %
                (self.id, self.name, self.age))

dept_doc_atable = Table('dept_doctors', Base.metadata,
    Column('dept_id', Integer, ForeignKey('dept.id')),
    Column('doctor_id', Integer, ForeignKey('doctor.id')))

class Doctor(Base):
    __tablename__ = 'doctor'

    id      = Column(Integer, primary_key=True)
    title   = Column(Unicode(5), default=u"Dr. ")
    name    = Column(Unicode(255), nullable=False)
    regdate = Column(myd, default=today)
    fee     = Column(Integer, default=0)   # Default per-consultation fee
    quals   = Column(Text())               # qualifications

    phone   = Column(Unicode(255))
    address = Column(Text())
    email   = Column(Unicode(255))

    consultations = relationship('Consultation',
                                 backref=backref('doctor',
                                                 cascade="all"))
    # 'slots' through backref from Slot
    # 'depts' through backref from Department

class Department(Base):
    __tablename__ = 'dept'

    id   = Column(Integer, primary_key=True)
    name = Column(Unicode(255), nullable=False)
    doctors = relationship('Doctor', secondary=dept_doc_atable,
                           backref=backref('depts', cascade="all"))

    ## No idea if this is the right way to do this, but anyway, here goes...
    @classmethod
    def id_from_name (self, session, name):
        rec = self.find_by_name(session, name)
        if rec:
            return rec.id
        else:
            return None

    @classmethod
    def find_by_name (self, session, name):
        """Returns the first record that matches given name. Returns None if
        there is no match."""

        print 'Looking for deparment: ', name
        q   = session().query(Department)
        recs = q.filter_by(name=name)
        if recs.count() > 0:
            print '  Found something.'
            return recs.first()

        return None

## The proper way for us to model this is to use a separate table for the
## working hours every day. But this is proving to be too complicated. For now
## this database table is only used to create the sampledb.
class Shift(Base):
    __tablename__ = 'shift'

    id    = Column(Integer, primary_key=True)
    name  = Column(Unicode(16))                     # ['Morning', 'Afternoon']
    start = Column(Unicode(4))
    end   = Column(Unicode(4))

class Slot(Base):
    __tablename__ = 'slot'

    id         = Column(Integer, primary_key=True)
    doctor_id  = Column(Integer, ForeignKey('doctor.id'))
    # shift_id   = Column(Integer, ForeignKey('shift.id'))
    day        = Column(Unicode(8))       # ['Sunday', 'Monday'... 'Saturday']
    shift      = Column(Unicode(16))      # ['Morning', 'Afternoon']
    start_time = Column(Unicode(8))
    end_time   = Column(Unicode(8))
    doctor     = relationship('Doctor',
                              backref=backref('slots', cascade="all"))

class Consultation(Base):
    __tablename__ = 'consultation'

    id         = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patient.id'))
    doctor_id  = Column(Integer, ForeignKey('doctor.id'))
    date       = Column(myd,  default=now())
    charge     = Column(Integer, default=0)
    notes      = Column(Text())

    ## backrefs from patient and doctor

def setup_tables (dbfile):
    """dbfile has to be relative to APP ROOT"""

    logging.debug('setup_tables with dbfile: %s', dbfile)

    logging.debug('Creating engine...')
    engine = create_engine('sqlite:///%s' % dbfile, echo=False)
    logging.debug('Creating engine...done (%s)', engine)

    # Set up the session
    logging.debug('Setting up tables...')
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    logging.debug('Setting up tables...done')

    session = orm.scoped_session(orm.sessionmaker(autoflush=True,
                                                  autocommit=False,
                                                  expire_on_commit=True,
                                                  bind=engine))

    return engine, session
