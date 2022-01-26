from flask import Flask, jsonify, make_response, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, ForeignKey, true
from flask_restful import Api, Resource
from flask_cors import CORS
from sqlalchemy.orm import backref
from datetime import date
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.curdir , 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

