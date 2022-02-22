from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime


class ClientDatabase:
    Base = declarative_base()

    class RegisteredUsers(Base):
        __tablename__ = 'Registered_users'
        id = Column(Integer, primary_key=True)
        username = Column(String)

        def __init__(self, user):
            self.id = None
            self.username = user

    class MessageHistory(Base):
        __tablename__ = 'Message_history'
        id = Column(Integer, primary_key=True)
        sender = Column(String)
        recipient = Column(String)
        message = Column(Text)
        date = Column(DateTime)

        def __init__(self, sender, recipient, message):
            self.id = None
            self.sender = sender
            self.recipient = recipient
            self.message = message
            self.date = datetime.datetime.now()

    class Contacts(Base):
        __tablename__ = 'Contacts'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True)

        def __init__(self, contact):
            self.id = None
            self.name = contact

    def __init__(self, name):
        self.database_engine = create_engine(f'sqlite:///client_{name}.db3', echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})
        self.Base.metadata.create_all(self.database_engine)
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            new_contact = self.Contacts(contact)
            self.session.add(new_contact)
            self.session.commit()

    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    def add_users(self, users_list):
        self.session.query(self.RegisteredUsers).delete()
        for user in users_list:
            self.session.add(self.RegisteredUsers(user))
        self.session.commit()

    def save_message(self, sender, recipient, message):
        self.session.add(self.MessageHistory(sender, recipient, message))
        self.session.commit()

    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def get_users(self):
        return [user[0] for user in self.session.query(self.RegisteredUsers.username).all()]

    def check_user(self, user):
        return True if self.session.query(self.RegisteredUsers).filter_by(username=user).count() else False

    def check_contact(self, contact):
        return True if self.session.query(self.Contacts).filter_by(name=contact).count() else False

    def get_history(self, sender=None, recipient=None):
        query = self.session.query(self.MessageHistory)
        if sender:
            query = query.filter_by(sender=sender)
        if recipient:
            query = query.filter_by(recipient=recipient)
        return [(data_row.sender, data_row.recipient, data_row.message, data_row.date) for data_row in query.all()]

