from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from app import app, db
import datetime
from admin.models import User, Role, ROLES
from flask_user import UserManager

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def preload():
    user_manager = UserManager(app, db, User)
    if not User.query.filter(User.email == 'admin@example.com').first():
        user = User(
            email='admin@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )

        user.roles.append(Role(name='admin'))
        db.session.add(user)
        db.session.commit()
    for role in ROLES:
        if not Role.query.filter(Role.name == role).first():
            r = Role(name=role)
            db.session.add(r)
            db.session.commit()


if __name__ == "__main__":
    manager.run()
