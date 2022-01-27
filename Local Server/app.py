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
import uuid

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
    print(encoded_jwt)

    resp = make_response(jsonify({'token': encoded_jwt}), 200)
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
 