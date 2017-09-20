#!/usr/bin/env python3

from flask import Flask, render_template, redirect
from flask import request as r
import requests
from hashlib import sha256
from html import escape
import random

app = Flask(__name__)

NETATMO_CLIENT_ID = "59c2c86f49c75f2f158bb615"
NETATMO_SECRET = "5zwtK9How97KKsoFO3dgN5IsLOANO5Gm8CYiD50hkwM1"

#	TODO: this should be per client & stored inside session
STATE = sha256(hex(random.getrandbits(128)).encode('ascii')).hexdigest()

NETATMO_API_CLASSES = [
        ('Weather devices', 'getstationsdata'),
        ('Thermostat devices', 'getthermostatsdata'),
        ('Health Home coach', 'gethomecoachsdata'),
        ]

def postRequest(url, params={}, data={}):
    """ Wrapper to simlify POST requests for URLs. It returns pair of boolean
    and response object: (status, response). When status is True it means that
    there was no HTTP error. """
    try:
        response = requests.post(url, params=params, data=data)
        response.raise_for_status()
        return (True, response)

    except requests.exceptions.HTTPError as error:
        print("[-]", url)
        print("[-]", error.response.status_code, error.response.text)
        return (False, error.response)

def retriveToken(code):
    """ Method for retriving authorization token from NETATMO cloud. 
    It takes one parameter - code, which is code retrived from NETATMO cloud
    user sign-in process """
    payload = {'grant_type': 'authorization_code',
            'client_id': NETATMO_CLIENT_ID,
            'client_secret': NETATMO_SECRET,
            'code': code,
            'redirect_uri': 'http://127.0.0.1:5000/signin'}
    ok, response = postRequest("https://api.netatmo.com/oauth2/token", data=payload)
    if ok:
        access_token=response.json()["access_token"]
        refresh_token=response.json()["refresh_token"]
        scope=response.json()["scope"]
        return access_token
    else:
        return None

def retriveDevices(access_token, api_call):
    """ Helper to retrive list of devices for given api_call using access_token
    """
    payload = {
            'access_token': access_token
            }
    ok, response = postRequest("https://api.netatmo.com/api/"+api_call, params=payload)
    if ok:
        return response
    return None

def dumpDevices(title, devs, toDisplay='station_name'):
    """ Helper for displaying user devices connected to NETATMO cloud.
    See also dumpCameras """
    out = "<b>" + title + "</b><ul>"
    for i in devs:
        out += "<li>" + escape(i[toDisplay]) + "</li>"
    out += "</ul>"
    return out

def dumpCameras(data):
    """ Helper for displaying user cameras connected to NETATMO cloud. See also
    dumpDevices """
    devs = []
    try:
        devs = data.json()["body"]["homes"]["cameras"]
    except KeyError as e:
        pass
    except TypeError as e:
        pass
    return dumpDevices('Cameras', devs, toDisplay='name')

@app.route('/')
def sign():
    return "<form action='/signin' method='get'><button type='submit'>Sign in</button></form>"

@app.route('/signin', methods=['GET'])
def signin():
    # Test if "code" is provided in get parameters (that would mean that user has already accepted the app and has been redirected here)
    if r.args.get('code') and r.args.get('state'):

        if r.args.get('state') != STATE:
            return "Invalid state returned"

        access_token = retriveToken(r.args.get('code'))

        if not access_token:
            return "Unable to retrive token"

        out = ""
        #   retriving normal devices
        for i in NETATMO_API_CLASSES:
            info = retriveDevices(access_token, i[1])
            if info:
                out += dumpDevices(i[0], info.json()["body"]["devices"])
        #   retriving cameras
        info = retriveDevices(access_token, 'gethomedata')
        if info:
            out += dumpCameras(info)

        return out

    # Test if "error" is provided in get parameters (that would mean that the user has refused the app)
    elif r.args.get('error'):
        return "ERROR: " + r.args.get('error')
    # If "error" and "code" are not provided in get parameters: the user should be prompted to authorize your app
    else:
        payload = {'client_id': NETATMO_CLIENT_ID,
                'redirect_uri': "http://127.0.0.1:5000/signin",
                'scope': 'read_station read_thermostat read_camera read_presence read_homecoach',
                'state': STATE}
        ok, response = postRequest("https://api.netatmo.com/oauth2/authorize", params=payload)
        if ok:
            return redirect(response.url, code=302)
        else:
            return response.text

if __name__ == "__main__":
    app.run()
