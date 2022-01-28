from flask import Flask, jsonify, make_response, request
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer, Boolean, DateTime,Time, Float, ForeignKey, true
from flask_restful import Api, Resource
from flask_cors import CORS
from sqlalchemy.orm import backref
from datetime import datetime
import os
import jwt
import uuid
from functools import wraps
import requests

##################################################
#REMOTE SERVER
##################################################

pv_key = 'NTNv7j0TuYARvmNMmWXo6fKvM4o6nv/aUi9ryX38ZH+L1bkrnD1ObOQ8JAUmHCBq7Iy7otZcyAagBLHVKvvYaIpmMuxmARQ97jUVG16Jkpkp1wXOPsrF9zwew6TpczyHkHgX5EuLg2MeBuiT/qJACs1J0apruOOJCg/gOtkjB4c='
localserver1token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6ImxvY2Fsc2VydmVyMSIsImV4cCI6MTY0OTEwNjI4MH0.7nGuCifHSYp9B3cbWGkOxAq_dSeCehq2VI7H5DOBL4o'

app = Flask(__name__)
CORS(app)

cors = CORS(app, resource={
    r"/*" : {
        "origins" : "*"
    }
})
api = Api(app)

app.config['SECRET_KEY'] = pv_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.curdir , 'remoteServer.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)


class Office(db.Model):
    __tablename__ = 'Office'
    id = Column(Integer, primary_key=True)
    lightsOnTime = Column(String, nullable=True)
    lightsOffTime = Column(String, nullable=True)

class User(db.Model):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True)
    guid = Column(String, unique=True)
    card = Column(String, unique=True)
    roomId = Column(Integer, nullable=False)
    lightValue = Column(Float ,nullable=False)
    officeId = Column(Integer, ForeignKey('Office.id'))
    office = db.relationship("Office", backref=backref("Office3", uselist=False))

class Admin(db.Model):
    __tablename__ = 'Admin'
    id = Column(Integer, primary_key=True)
    user = Column(String, unique=True)
    password = Column(String, nullable=False)
    officeId = Column(Integer, ForeignKey('Office.id'))
    office = db.relationship("Office", backref=backref("Office", uselist=False))

# True => admin
class Activity(db.Model):
    __tablename__ = 'Activity'
    id = Column(Integer, primary_key=True)
    type = Column(Boolean)
    datetime = Column(DateTime)
    officeId = Column(Integer, ForeignKey('Office.id'))
    office = db.relationship("Office", backref=backref("Office2", uselist=False))
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
            current_user = Admin.query\
                .filter_by(user = data['username'])\
                .first()
        except:
            return jsonify({'message' : 'Token is invalid !!'}), 401
        # returns the current logged in users contex to the routes
        return  f(current_user, *args, **kwargs)
  
    return decorated

def localserver_token_required(f):
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
            if data['id'] != 'localserver1':
                return jsonify({'message' : 'Token is invalid !!'}), 401
            print(data)
        except:
            return jsonify({'message' : 'Token is invalid !!'}), 401
        # returns the current logged in users contex to the routes
        return  f(true, *args, **kwargs)
  
    return decorated



@app.route('/api/office/register', methods=['POST'])
def registerOffice():
    try:
        body = request.get_json()
        lightOnTime = body['lightOnTime']
        lightOffTime = body['lightOffTime']
    except Exception as ex:
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp
    
    if (body == None) or (body['lightOnTime'] == None) or (body['lightOffTime'] == None):
        resp = make_response(jsonify({'message': 'Bad request2.'}), 400)
        return resp
    

    office = Office(lightsOnTime=lightOnTime, lightsOffTime=lightOffTime)
    db.session.add(office)
    db.session.commit()

    resp = make_response(jsonify({'message': 'Office created!'}), 200)
    return resp


@app.route('/api/admin/register', methods=['POST'])
def registerAdmin():
    try:
        body = request.get_json()
        username = body['username']
        password = body['password']
        officeId = body['officeId']
    except Exception as ex:
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp
    
    
    if (body == None) or (body['username'] == None) or (body['password'] == None) or (body['officeId'] == None):
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp

    office = Office.query.get(officeId)
    if office == None:
        resp = make_response(jsonify({'message': 'Office not found :)).'}), 400)
        return resp


    admin = Admin.query.filter_by(user=username).first()
    if admin != None:
        resp = make_response(jsonify({'message': 'Username already taken :)).'}), 400)
        return resp
    
    newAdmin = Admin(user=username, password=password, officeId = officeId)
    db.session.add(newAdmin)
    db.session.commit()

    resp = make_response(jsonify({'message': 'Admin created!'}), 200)
    return resp

@app.route('/api/admin/login', methods=['GET'])
def loginAdmin():
    try:
        body = request.get_json()
        user = body['user']
        password = body['password']
    except Exception as ex:
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp
    
    if (body == None) or (body['user'] == None) or (body['password'] == None):
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp


    user = Admin.query.filter_by(user=user).first()
    if user == None:
        resp = make_response(jsonify({'message': 'User not found.'}), 400)
        return resp
    if user.password != password:
        resp = make_response(jsonify({'message': 'Wrong password :(('}), 400)
        return resp
    
    encoded_jwt = jwt.encode({
    "username": user.user,
    "exp": 1649106280
    }, pv_key, algorithm="HS256")
    print(encoded_jwt)

    resp = make_response(jsonify({'token': encoded_jwt}), 200)
    return resp


@app.route('/api/admin/activities', methods=['GET'])
@token_required
def getActivities(current_user):
    try:
        activities = Activity.query.all()
        all = []
        for item in activities:
            all.append({
              'id': item.id ,
              'type': item.type,
              'datetime': item.datetime,
              'officeId': item.officeId,
              'userId': item.userId
            })

    except Exception as ex:
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp
    
    resp = make_response(jsonify({'allActivities': all}), 200)
    return resp

@app.route('/api/admin/setlights', methods=['PUT'])
@token_required
def editOfficeLightTime(current_user):
    try:
        body = request.get_json()
        officeid = body['officeId']
        lightOn = body['lightOn']
        lightOff = body['lightOff']
    except Exception as ex:
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp
    
    if (body == None) or (body['officeId'] == None) or (body['lightOff'] == None) or (body['lightOff'] == None):
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp


    office = Office.query.filter_by(id=officeid).first()
    if office == None:
        resp = make_response(jsonify({'message': 'Office not found.'}), 400)
        return resp
    
    office.lightsOnTime = lightOn
    office.lightsOffTime = lightOff
    db.session.commit()    
    

    resp = make_response(jsonify({'message': 'Time changed.'}), 200)
    return resp

@app.route('/api/admin/user/register', methods=['POST'])
@token_required
def registerUser(current_user):
    try:
        body = request.get_json()
        card = body['card']
        roomId = body['roomId']
        officeId = body['officeId']
        lightValue = body['lightValue']
    except Exception as ex:
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp
    
    
    if (body == None) or (card == None) or (roomId == None) or (lightValue == None) or (officeId == None):
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp

    office = Office.query.get(officeId)
    if office == None:
        resp = make_response(jsonify({'message': 'Office not found :)).'}), 400)
        return resp


    user = User.query.filter_by(card=card).first()
    if user != None:
        resp = make_response(jsonify({'message': 'Card already taken :)).'}), 400)
        return resp

    guid = uuid.uuid4()
    newUser = User(card=card, roomId=roomId, officeId = officeId, lightValue=lightValue, guid=str(guid))

    resp = requests.post('http://localhost:5001/api/user/add',json={"card":card, "roomId":roomId, "guid":str(guid)})
    print(resp.status_code)
    if resp.status_code == 200:
        db.session.add(newUser)
        db.session.commit()
        resp = make_response(jsonify({'message': 'User created!'}), 200)
    else:
        resp = make_response(jsonify({'message': 'CAN NOT BE CREATED!'}), 400)

    return resp


##################################################################
#####################        CUSTOM APIS     #####################
##################################################################

@app.route('/api/user/getlight', methods=['GET'])
@localserver_token_required
def getLight(ok):
    try:
        body = request.get_json()
        print(body)
        guid = body['guid']
    except Exception as ex:
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp
    
    if (body == None) or (body['guid'] == None):
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp

    
    user = User.query.filter_by(guid=guid).first()

    if user == None:
        resp = make_response(jsonify({'message': 'User not found',}), 400)
        return resp
    
    resp = make_response(jsonify({
        'lightValue': user.lightValue,
    }), 200)
    return resp
 
@app.route('/api/user/addActivity', methods=['POST'])
@localserver_token_required
def addActivityToTable(ok):
    try:
        body = request.get_json()
        print(body)
        userId = body['userId']
        officeId = body['officeId']
    except Exception as ex:
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp
    
    if (body == None) or (userId == None) or ( officeId == None):
        resp = make_response(jsonify({'message': 'Bad request.'}), 400)
        return resp


    lastActivity = Activity.query.filter_by(userId=userId).order_by(Activity.datetime.desc()).first()
    print(lastActivity)
    if lastActivity == None:
        newItem = Activity(userId=userId, officeId=officeId, datetime=datetime.now(), type=True)
    else:
        newItem = Activity(userId=userId, officeId=officeId, datetime=datetime.now(), type= not lastActivity.type)
    
    db.session.add(newItem)
    db.session.commit()
            
    
    resp = make_response(jsonify({
        'message': 'Activity added for user: ( ' + str(userId) + ' ) in office: ( ' + str(officeId) + ' ) at ( ' + str(datetime) + ' )',
    }), 200)
    return resp
 