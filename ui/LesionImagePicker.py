#!/usr/bin/env python

# Flask / mongodb based script to serve a set of images to web clients
#
# - each sub-set of images makes a "lesion" (at a specific time point)
# - clients will display the sub-set of images
# - each image will have a link target <a> defined that serves the
#   next page, while recording the selection on the backend side
# - below the image will be a link to show the image in full size
#
# - cookies: user (email address), uid (6-digit session id, from MD5)
# - query fields: lesion (########-########-########), sel (########)


# imports
import copy
import glob
import hashlib
import os
from random import random

from flask import Flask, make_response, render_template, request # , redirect, url_for
from pymongo import MongoClient


# settings
#image_folder = '/Users/Jochen/Data/MSKCC/azure/html/static/images'
#image_folder = 'C:\\Users\\weberj3\\Documents\\git\\lesionimagepicker\\ui\\static\\noheader'
image_folder = '/home/jochen/lesionimagepicker/ui/static/noheader'
mongoloc = 'mongodb://127.0.0.1:27017'
number_reads = 1
template = 'lip.html'
title = 'Lesion Image Picker'
heading = 'Please pick an image for this lesion'

# users
users = [
    'chousake@mskcc.org',
    'kurtansn@mskcc.org',
    'musthaqs@mskcc.org',
    'nandaj@mskcc.org',
    'reiterao@mskcc.org',
    'rotembev@mskcc.org',
    'weberj3@mskcc.org',
]
user_salt = 'MSKCC_LIP'


# find images, and store relative filename only
imagefiles = glob.glob(image_folder + os.sep + '*' + os.sep + '*.jpg')
images = copy.deepcopy(imagefiles)
for idx, image in enumerate(images):
    images[idx] = image.rpartition(os.sep)[2]

# parse into lesions
lesions = dict()
lesion_images = dict()
for idx, image in enumerate(images):
    image_name = image.partition('.')[0]
    lesion_images[image_name] = True
    if '_' in image_name:
        image_parts = image_name.split('_')
    else:
        print('Invalid image name: ' + image_name)
        continue
    lesion_id = image_parts[0] + '_' + image_parts[1] + '_' + image_parts[2]
    image_id = image_parts[3]
    if not lesion_id in lesions:
        lesions[lesion_id] = dict()
    lesions[lesion_id][image_id] = [image_name, imagefiles[idx]]
print('{0:d} lesions (with {1:d} images) found.'.format(
    len(lesions), len(images)))

# connect to mongodb, and select collection (selected)
client = MongoClient(mongoloc)
db = client.lesion_image_picker
selected = db.selected

# find out which images remain
remaining = dict()
for lesion_id in lesions.keys():
    remaining[lesion_id] = number_reads
in_db = selected.find()
for record in in_db:
    lesion_id = record['lesion']
    if lesion_id not in remaining:
        print(lesion_id)
        continue
    remaining[lesion_id] -= 1
total_remaining = 0
for lesion_id in list(remaining.keys()):
    if remaining[lesion_id] <= 0:
        del remaining[lesion_id]
    else:
        total_remaining += remaining[lesion_id]
print('{0:d} lesions remain to be picked (with {1:d} picks).'.format(
    len(remaining), total_remaining))

# check username/session
def check_user(user, uid):
    if not user or not uid:
        return False
    elif user not in users:
        return False
    usp = user + user_salt
    m = hashlib.md5(usp.encode('utf-8'))
    umd5 = m.hexdigest()
    if uid.lower() == umd5[0:6].lower():
        return True
    else:
        return False

# find next page for session ID
def check_page(uid, page):
    if not page in lesions:
        return next_page(uid)
    in_db = selected.find({'lesion': page})
    for record in in_db:
        if record['uid'] == uid:
            return next_page(uid)
    return page

def next_page(uid):
    uremaining = dict()
    for rk in remaining.keys():
        uremaining[rk] = True
    if uid:
        in_db = selected.find({'uid': uid})
        for record in in_db:
            if record['lesion'] in uremaining:
                del uremaining[record['lesion']]
    print(len(uremaining))
    if len(uremaining) == 0:
        return 'NULL'
    rkeys = list(uremaining.keys())
    return rkeys[int(len(rkeys) * random())]


# generate Flask app
app = Flask(__name__)

# and define routes
@app.route('/index.html')
@app.route('/')
def entry():
    user = request.cookies.get('user')
    uid = request.cookies.get('uid')
    if user and uid and check_user(user, uid):
        resp = render_template(template, entry=True, title=title, user=user, uid=uid)
    else:
        resp = render_template(template, entry=True, title=title)
    return resp

@app.route('/page.html')
def page():
    user = request.args.get('username')
    uid = request.args.get('sessionid')
    if not (user and uid):
        user = request.cookies.get('user')
        uid = request.cookies.get('uid')
        user_set = False
    else:
        user_set = True
    if not user or user == '':
        user = 'NULL'
    if not check_user(user, uid):
        resp = render_template(template, baduser=user)
        user_set = False
    else:
        lesion_id = request.args.get('lesion')
        if not lesion_id:
            lesion_id = 'NULL'
        sel = request.args.get('sel')
        if not sel:
            sel = 'NULL'
        lesion_image = lesion_id + '_' + sel
        if lesion_id in remaining and (lesion_image in lesion_images or sel == '00000000' or sel == 'multiple'):
            if sel == '00000000':
                comm = request.args.get('comment')
                if comm:
                    selected.insert_one(
                        {'lesion': lesion_id, 'uid': uid, 'selected': sel, 'comment': comm})
            elif sel == 'multiple':
                comm = request.args.get('comment')
                sel = ''
                for msc in range(32):
                    ssel = request.args.get('multi' + str(msc))
                    if ssel:
                        if sel:
                            sel += '+'
                        sel += ssel
                selected.insert_one(
                    {'lesion': lesion_id, 'uid': uid, 'selected': sel, 'comment': comm})
            else:
                selected.insert_one({'lesion': lesion_id, 'uid': uid, 'selected': sel})
            remaining[lesion_id] -= 1
            if remaining[lesion_id] <= 0:
                del remaining[lesion_id]
        
        page = request.args.get('next')
        if not page:
            page = next_page(uid)
        else:
            page = check_page(uid, page)
        if page == 'NULL':
            resp = render_template(template, finished=True)
        else:
            images = lesions[page]
            resp = render_template(template, page=page, images=images,
                image_keys=list(images.keys()), num_images=len(images),
                remaining=len(remaining))
    if user_set:
        resp = make_response(resp)
        resp.set_cookie('user', user, 365*86400)
        resp.set_cookie('uid', uid, 7*86400)
    return resp

# call app.run if __main__
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
