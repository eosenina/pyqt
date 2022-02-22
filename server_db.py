from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime


class ServerStorage:
    Base = declarative_base()

    class AllUsers(Base):
        __tablename__ = 'Users'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True)
        last_login = Column(DateTime)

        def __init__(self, username):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.id = None

        def __repr__(self):
            return f"User: {self.name}, Last login: {self.last_login}"

    class ActiveUsers(Base):
        __tablename__ = 'Active_users'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('Users.id'), unique=True)
        ip_address = Column(String)
        port = Column(Integer)
        login_time = Column(DateTime)

        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    class LoginHistory(Base):
        __tablename__ = 'Login_history'
        id = Column(Integer, primary_key=True)
        name = Column(ForeignKey('Users.id'))
        date_time = Column(DateTime)
        ip = Column(String)
        port = Column(String)

        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    class UsersContacts(Base):
        __tablename__ = 'Contacts'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('Users.id'))
        contact = Column(ForeignKey('Users.id'))

        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    class UsersHistory(Base):
        __tablename__ = 'History'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('Users.id'))
        sent = Column(Integer)
        accepted = Column(Integer)

        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self):
        self.database_engine = create_engine('sqlite:///server_base.db3', echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})
        self.Base.metadata.create_all(self.database_engine)
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip, port):
        search_user = self.session.query(self.AllUsers).filter_by(name=username)
        if search_user.count():
            user = search_user.first()
            user.last_login = datetime.datetime.now()
        else:
            # new user
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()
            users_history = self.UsersHistory(user.id)
            self.session.add(users_history)
        new_active_user = self.ActiveUsers(user.id, ip, port, datetime.datetime.now())
        self.session.add(new_active_user)
        history = self.LoginHistory(user.id, datetime.datetime.now(), ip, port)
        self.session.add(history)
        self.session.commit()

    def user_logout(self, username):
        user = self.session.query(self.AllUsers).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def users_list(self):
        return self.session.query(self.AllUsers.name, self.AllUsers.last_login).all()

    def active_users_list(self):
        query = self.session.query(
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        return query.all()

    def login_history(self, username=None):
        query = self.session.query(self.AllUsers.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.AllUsers)
        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()

    def process_message(self, sender, recipient):
        sender = self.session.query(self.AllUsers).filter_by(name=sender).first().id
        recipient = self.session.query(self.AllUsers).filter_by(name=recipient).first().id

        sender_history = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        if not sender_history:
            new_history_row = self.UsersHistory(sender)
            new_history_row.sent = 1
            self.session.add(new_history_row)
            self.session.commit()
        else:
            sender_history.sent += 1

        recipient_history = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        if not recipient_history:
            new_history_row = self.UsersHistory(recipient)
            new_history_row.accepted = 1
            self.session.add(new_history_row)
            self.session.commit()
        else:
            recipient_history.accepted += 1

        self.session.commit()

    def add_contact(self, user, contact):
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()
        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).count():
            return
        new_contact = self.UsersContacts(user.id, contact.id)
        self.session.add(new_contact)
        self.session.commit()

    def remove_contact(self, user, contact):
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()
        if not contact:
            return
        print(self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete())
        self.session.commit()

    def get_contacts(self, username):
        user = self.session.query(self.AllUsers).filter_by(name=username).one()
        query = self.session.query(self.UsersContacts,
                                   self.AllUsers.name).filter_by(user=user.id).join(self.AllUsers,
                                                                                    self.UsersContacts.contact == self.AllUsers.id)
        return [contact[1] for contact in query.all()]

    def message_history(self):
        query = self.session.query(self.AllUsers.name, self.AllUsers.last_login, self.UsersHistory.sent,
                                   self.UsersHistory.accepted).join(self.AllUsers)
        return query.all()
