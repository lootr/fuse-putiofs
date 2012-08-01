# -*- encoding: utf-8 -*-

class AuthenticationFailed(Exception):
    def __init__(self):
        super(AuthenticationFailed, self).__init__("Authentication has failed")
