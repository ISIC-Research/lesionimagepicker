#!/usr/bin/env python

# prints the UID for an email address

# imports
import argparse
import hashlib

# salt
user_salt = 'MSKCC_LIP'

# main (print MD5)
def main():

    a = argparse.ArgumentParser(prog='LIPUID', description='Print UID for LIP')
    a.add_argument('-u', '--user', help='user (email)')
    try:
        o = a.parse_args()
    except Exception as e:
        print('Error parsing input arguments: ' + str(e))
        return 1
    user = o.user
    if not user:
        a.print_help()
    else:
        m = hashlib.md5(user + user_salt)
        umd5 = m.hexdigest()
        print(umd5[0:6].lower())

if __name__ == '__main__':
    import sys
    sys.exit(main())

