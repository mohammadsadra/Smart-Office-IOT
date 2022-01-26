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
from functools import wraps

##################################################
#REMOTE SERVER
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.curdir , 'remoteServer.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
ma = Marshmallow(app)


class User(db.Model):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True)
    guid = Column(String, unique=True)
    card = Column(String, unique=True)
    roomId = Column(Integer, nullable=False)
    lightValue = Column(Float ,nullable=False)


class Office(db.Model):
    __tablename__ = 'Office'
    id = Column(Integer, primary_key=True)
    lightsOnTime = Column(String, nullable=True)
    lightsOffTime = Column(String, nullable=True)

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
            current_user = User.query\
                .filter_by(guid = data['guid'])\
                .first()
        except:
            return jsonify({'message' : 'Token is invalid !!'}), 401
        # returns the current logged in users contex to the routes
        return  f(current_user, *args, **kwargs)
  
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
    "guid": user.user,
    "exp": 1649106280
    }, pv_key, algorithm="HS256")
    print(encoded_jwt)

    resp = make_response(jsonify({'token': encoded_jwt}), 200)
    return resp
