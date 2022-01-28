#
# Copyright 2021 HiveMQ GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import time
import paho.mqtt.client as paho
from paho import mqtt

# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid)+ str(client))

# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

# using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
# userdata is user defined data of any type, updated by user_data_set()
# client_id is the given name of the client
client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect

# enable TLS for secure connection
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
client.username_pw_set("imohammadsadra", "Sadra7899")
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
client.connect("5c2c7c2605694c43ba60ad1f9f812f87.s2.eu.hivemq.cloud", 8883)

# setting callbacks, use separate functions like above for better visibility
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_publish = on_publish

# subscribe to all topics of encyclopedia by using the wildcard "#"
client.subscribe("encyclopedia/#", qos=1)

# a single publish, this can also be done in loops, etc.


# loop_forever for simplicity, here you need to stop the loop manually
# you can also use loop_start and loop_stop
client.loop_start()





from flask import Flask, jsonify, make_response, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, ForeignKey, true
from flask_restful import Api, Resource
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from sqlalchemy.orm import backref
from datetime import datetime, timedelta
import os
import jwt
from functools import wraps
import requests

##################################################
#LOCAL SERVER
##################################################

pv_key = 'NTNv7j0TuYARvmNMmWXo6fKvM4o6nv/aUi9ryX38ZH+L1bkrnD1ObOQ8JAUmHCBq7Iy7otZcyAagBLHVKvvYaIpmMuxmARQ97jUVG16Jkpkp1wXOPsrF9zwew6TpczyHkHgX5EuLg2MeBuiT/qJACs1J0apruOOJCg/gOtkjB4c='


app = Flask(__name__)
CORS(app)

cors = CORS(app, resource={
    r"/*" : {
        "origins" : "*"
    }
})
api = Api(app)

app.config['SECRET_KEY'] = pv_key
app.config['JSON_SORT_KEYS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.curdir , 'localServer.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)

class User(db.Model):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True)
    guid = Column(String, unique=True)
    card = Column(String, unique=True)
    roomId = Column(Integer, nullable=False)

class Cache(db.Model):
    __tablename__ = 'Cache'
    id = Column(Integer, primary_key=True)
    lightValue = Column(Float ,nullable=False)
    expireDate = Column(DateTime, nullable=False)
    userId = Column(String, ForeignKey('User.guid'))
    user = db.relationship("User", backref=backref("User", uselist=False))

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
            token = token.split(' ')[1]
        # return 401 if token is not passed
        if not token:
            return jsonify({'message' : 'Token is missing !!'}), 401
  
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, pv_key, algorithms=["HS256"])
            current_user = User.query\
                .filter_by(guid = data['guid'])\
                .first()
        except:
            return jsonify({'message' : 'Token is invalid !!'}), 401
        # returns the current logged in users contex to the routes
        return  f(current_user, *args, **kwargs)
  
    return decorated


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'lightValue', 'expireDate', 'userId')


@app.route('/api/user/login', methods=['GET'])
def loginUser():
    # client.publish("encyclopedia/temperature", payload="Mn omadam tooooooo!", qos=1)
    try:
        body = request.get_json()
        guid = body['guid']
        card = body['card']
    except Exception as ex:
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp
    
    if (body == None) or (body['guid'] == None) or (body['card'] == None):
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp


    user = User.query.filter_by(guid=guid).first()
    if user == None:
        resp = make_response(jsonify({'message': 'User not found.'}), 400)
        return resp
    
    encoded_jwt = jwt.encode({
    "guid": user.guid,
    "exp": 1649106280
    }, pv_key, algorithm="HS256")
    
    cachedUser = Cache.query.filter_by(userId=user.guid).first()
    
    print((datetime.now()  + timedelta(hours=12)))
    if cachedUser == None or cachedUser.expireDate < datetime.now():
        resp = requests.get('http://localhost:5000/api/user/getlight',json={"guid":user.guid})
        if resp.status_code == 200:
            newCache = Cache(lightValue=resp.json()['lightValue'], expireDate=datetime.now()+timedelta(hours=12), userId=user.guid)
            ### LOCAL SERVER SENDS ITS OWN OFFICE ID
            activityResponse = requests.post('http://localhost:5000/api/user/addActivity',json={"userId":user.guid, "officeId":1})
            if activityResponse.status_code != 200:
                resp = make_response(jsonify({'message': 'Failed setting ACTIVITY from remote server!!!'}), 400)
                return resp
            db.session.add(newCache)
            db.session.commit()
            resp = make_response(jsonify({'token': encoded_jwt, 'lightValue': newCache.lightValue, 'message': 'Returned from remote server'}), 200)
            # client.publish("smartoffice/light", payload=newCache.lightValue, qos=1)
            return resp
        else:
            resp = make_response(jsonify({'message': 'Failed getting light from remote server!!!'}), 400)
            return resp
    else:
        resp = make_response(jsonify({'token': encoded_jwt, 'lightValue': cachedUser.lightValue, 'message': 'Returned from CACHE'}), 200)
        activityResponse = requests.post('http://localhost:5000/api/user/addActivity',json={"userId":user.guid, "officeId":1})
        if activityResponse.status_code != 200:
            resp = make_response(jsonify({'message': 'Failed setting ACTIVITY in remote server!!!'}), 400)
            return resp
        # else:
        #     client.publish("smartoffice/light", payload=cachedUser.lightValue, qos=1)

        return resp
    

#DIFFERNT FROM HW
@app.route('/api/user', methods=['POST'])
@token_required
def setLight(current_user):
    
    try:
        body = request.get_json()
        light = body['value']
    except Exception as ex:
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp
    
    if (body == None) or (body['value'] == None):
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp

    record = Cache.query\
                .filter_by(userId = current_user.guid)\
                .first()
    if record == None:
        newItem = Cache(lightValue= light, expireDate= datetime.now() + timedelta(hours=12), userId= current_user.guid)
        db.session.add(newItem)
    else:
        record.lightValue = light
        record.expireDate= datetime.now() + timedelta(hours=12)
    
    db.session.commit()
            
    
    resp = make_response(jsonify({
        'expireDate': datetime.now() + timedelta(hours=12),
    }), 200)
    # client.publish("smartoffice/light", payload=float(light), qos=1)
    return resp
 


##################################################################
#####################        CUSTOM APIS     #####################
##################################################################

@app.route('/api/user/add', methods=['POST'])
def addUserToTable():
    try:
        body = request.get_json()
        print(body)
        guid = body['guid']
        card = body['card']
        roomId = body['roomId']
    except Exception as ex:
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp
    
    if (body == None) or (body['guid'] == None) or ( body['card'] == None) or (body['roomId'] == None):
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp


    
    newItem = User(guid= guid, card= card, roomId=roomId)
    db.session.add(newItem)
    db.session.commit()
            
    
    resp = make_response(jsonify({
        'message': 'User added to table in local server :))',
    }), 200)
    return resp
