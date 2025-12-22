from flask import current_app
from flask_login import UserMixin


class DictUser(UserMixin):
    # This class is not ORM, this is a wrapper for flask_login to work
    def __init__(self, user_dict):
        self.username = user_dict['username']
        self.password = user_dict['password']
        self.is_admin = user_dict.get('is_admin', False)
        self.active = True

    def get_id(self):
        return self.username

    @property
    def is_active(self):
        return self.active
