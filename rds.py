import pymysql
import time
import string
from hashlib import md5
import random
import os
class RDS:
    def __init__(self):
        """ Init """
        self.db = pymysql.connect(
            host=os.environ.get('ZWEEB_DB_HOST'),
            user=os.environ.get('ZWEEB_DB_USER'),
            password=os.environ.get('ZWEEB_DB_PW'),
            db=os.environ.get('ZWEEB_DB_NAME')
        )
        # prepare a cursor object using cursor() method
        self.cursor = self.db.cursor(pymysql.cursors.DictCursor)
        self.generic_bad_response = {'success' : False, 'msg' : ''}
        self.generic_good_response = {'success' : True, 'msg' : 'ok'}
        self.now = str(int(time.time()))
        self.shard_count = 1

        self.USER_OBJ = 1
        self.POST_OBJ = 2
        return 

    def getGlobId(self, local_id : int, obj_type : int) -> str:
        """
        Return a global id
        
        :param local_id int
        :param obj_type int
        :return string
        """
        shard_id = str(1)
        #t = str( (int(time.time())-1625356800) % 1024)
        return "( (" + shard_id + " << 46) | (" + obj_type + " << 36) | (%s << 0) ) as globId" \
        % (local_id)

    def parseGlobId(self, glob_id : str) -> dict:
        """
        Parse a global 64 bit id

        :param glob_id string
        :return dict
        """
        # 18 bits - this could be anything later on
        rand_id = (glob_id >> 46) & 0xFFFF
        # 10 bits
        shard_id = (glob_id >> 36) & 0x3FF
        # 32
        local_id = (glob_id >> 0 ) & 0xFFFFFFFFF

        # for now just returning local id
        return local_id

    def createId(self, seq_name):
        # seconds
        our_epoch = 1625356800
        shard_id = 1
        _id = (int(time.time()) - our_epoch) << (32-16)
       # _id |= (shard_id << 10) 
        sql = """SELECT nextval(%s) as seq_id"""
        self.cursor.execute(sql, (seq_name))
        row = self.cursor.fetchone()
        seq_id = row['seq_id']
        _id |= (seq_id % 1024)
        return _id

    def addNotifcationRow(self, args : dict):
        """
        Add a row to the notification table

        committed from calling method
        :param args dict
        :return 
        """
        q = """insert into notifications(uid, sk, to_user_id, notification, \
        date_added, from_user_id) values(%s,%s, %s,%s,%s,%s)"""
        self.cursor.execute(q, 
            (args['uid'], args['sk'], args['to_user_id'], args['msg'], self.now, args['from_user_id'])
        )

    def isUserBlocked(self, blocker_user_id : int, blocked_user_id : int):
        """
        first checked if the user can be followed by this user
        :return dict|None
        """
        q1 = """select 1 from blocked_users where user_id=%s and blocked_user_id=%s"""
        self.cursor.execute(q1, (blocker_user_id, blocked_user_id))
        row = self.cursor.fetchone()
        return row    

    def handleBioUpdate(self, bio : str, user_id: int) -> bool:
        """
        Update bio 
        
        :param bio str
        :param id int:str
        :return bool
        """  

        query = """update user set bio = %s where id = %s"""
        tuple1 = (bio, user_id)
        resp = self.generic_good_response
        try:
            self.cursor.execute(query, tuple1)
            self.db.commit()
        except: 
            self.db.rollback()
            resp = self.generic_bad_response
        self.db.close()
        return resp

    def handleNameUpdate(self, name : str, user_id: int) -> bool:
        """
        Update name 
        
        :param name str
        :param id int:str
        :return bool
        """  

        query = """update user set name = %s where id = %s"""
        tuple1 = (name, user_id)
        resp = self.generic_good_response
        try:
            self.cursor.execute(query, tuple1)
            self.db.commit()
        except: 
            self.db.rollback()
            resp = self.generic_bad_response
        self.db.close()
        return resp

    def handleWebsiteUpdate(self, website : str, user_id: int) -> bool:
        """
        Update website 
        
        :param website str
        :param id int:str
        :return bool
        """  
        query = """update user set website = %s where id = %s"""
        tuple1 = (website, user_id)
        resp = self.generic_good_response
        try:
            self.cursor.execute(query, tuple1)
            self.db.commit()
        except: 
            self.db.rollback()
            resp = self.generic_bad_response
        self.db.close()
        return resp

    def handleUsernameUpdate(self, username : str, user_id: int) -> bool:
        """
        Update username 
        
        :param username str
        :param id int:str
        :return bool
        """  
        query = """update user set username = %s where id = %s"""
        tuple1 = (username, user_id)
        resp = self.generic_good_response
        try:
            self.cursor.execute(query, tuple1)
            self.db.commit()
        except: 
            self.db.rollback()
            resp = self.generic_bad_response
        self.db.close()
        return resp

    def checkMyContacts(self, user_id : int, contact_data : list) -> dict:
        """
        Check if my contacts are on the app
        - returns list of contacts that are users
        :param user_id int
        :param contact_data list
        :return dict
        """
        phone_numbers = [x['phone_number'] for x in contact_data]
        phone_str = ','.join(['%s'] * len(phone_numbers))
        query = """select id, username, name, bio, follower_count, \
        following_count, profile_url, phone_number, likes_count, listens_count \
        from user as u \
        inner join followers as f
        ON f.followed_id = u.id
        where f.following_id = %%s
        and phone_number in (%s)
        """ % phone_str

        args = [user_id]+phone_numbers
        try:
            self.cursor.execute(query, args)
            data = self.cursor.fetchall()
        except: 
            data = []
        # db doesnt close because method below is called afterward on same connection
        #self.db.close()
        return data

    def addMyContacts(self, user_id : int, contact_data : list) -> dict:
        """
        Add my contacts to the system

        :param user_id str
        :param contact_data list
        :return list
        """
        query = """insert ignore into contacts(user_id, phone_number, name, email, date_added) \
        values(%s, %s, %s, %s, %s)"""
        date_added = str(int(time.time()))
        tuple1 = [(user_id, c['phone_number'], c['name'], c['email'], date_added) for c in contact_data] 
        resp = self.generic_good_response
        try:
            self.cursor.executemany(query, tuple1)
            self.db.commit()
        except: 
            self.db.rollback()
            resp = self.generic_bad_response
        self.db.close()
        return resp

    def updateNotificationSetting(self, user_id: int, on : int) -> dict:
        """
        Update a user notification setting, on off

        :param user_id int
        :param on int
        :return dict
        """
        query = """update user set notifications_on = %s where id = %s"""
        tuple1 = (on, user_id)
        resp = self.generic_good_response
        try:
            self.cursor.execute(query, tuple1)
            self.db.commit()
        except: 
            self.db.rollback()
            resp = self.generic_bad_response
        self.db.close()
        return resp

    def getRandomUID(self, some_str : str, size=6) -> str:
        """
        Generate random uid(ok for now)

        :param some_str str - another str to use in hash
        :param size int
        :return string
        """
        chars=string.ascii_uppercase + string.digits + string.ascii_lowercase
        ran = ''.join(random.choice(chars) for _ in range(size))
        x = str(time.time()) + ran + some_str
        return md5(x.encode()).hexdigest()

    def reportUser(self, user_id : int, reported_user : int, reason: str) -> dict:
        """
        Report another user

        :param user_id int
        :param reported_user int
        :param reason str
        :return list
        """
        query = """insert into reported_user(reported_user_id, from_user, \
        reason, date_added) \
        values(%s, %s, %s, %s)"""
        date_added = str(int(time.time()))
        resp = self.generic_good_response
        try:
            self.cursor.execute(query, (reported_user, user_id, reason, date_added))
            self.db.commit()
        except: 
            self.db.rollback()
            resp = self.generic_bad_response
        self.db.close()
        return resp
