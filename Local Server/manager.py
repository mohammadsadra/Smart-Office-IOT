from app import db , app
from flask_script import Manager

manger = Manager(app)

@manger.command
def init():
    db.create_all()
    print('Database Created Successfully!')

if __name__ == '__main__':
    manger.run()