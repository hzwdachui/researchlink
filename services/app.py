# coding=utf-8

from flask import Flask, current_app

from flask_migrate import Migrate
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask.logging import default_handler
from flask_login import current_user, login_required
from logging import Formatter, FileHandler
from configs.config import configs
from gevent.pywsgi import WSGIServer

from flaskweb.app import db, admin
from configs.config import DebugConfig

from . import views


def init_app(config=DebugConfig):
    app = create_app(config)
    app.register_blueprint(views.bp)
    # admin
    # admin.add_view(ModelView(models.Todo, db.session))
    # admin.add_view(ModelView(models.TodoItem, db.session))
    return app


def create_app(config, disable_debug_bp=False):
    app = Flask(
        __name__,
        static_folder=None,
        template_folder=None,
    )
    if isinstance(config, str):
        config = configs[config]
    app.config.from_object(config)

    # logging
    create_logger(app)

    # db
    db.init_app(app)
    app.logger.info("init db %s" % config.SQLALCHEMY_DATABASE_URI)
    migrate = Migrate(app, db)

    # views
    import services.views as main_views
    import auth.models as auth_models
    import auth.views as auth_views

    if not disable_debug_bp:
        auth_views.login_manager.init_app(app)
        app.register_blueprint(main_views.bp)
        app.register_blueprint(auth_views.bp)

    # admin
    admin.init_app(app, index_view=AdminIndex())
    admin.add_view(AdminOnlyModelView(auth_models.User, db.session))

    return app


def create_logger(app):
    formatter = Formatter(
        '[%(asctime)s] [%(filename)s:%(lineno)d] [%(levelname)s]\t%(message)s')
    default_handler.setFormatter(formatter)

    file_handler = FileHandler(app.config["LOGGING_FILE"])
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(app.config["LOGGING_LEVEL"])


def gevent_run(app, host="127.0.0.1", port=5000):
    print("gevent server staring on http://%s:%s" % (host, port))
    WSGIServer((host, int(port)), app).serve_forever()


class AdminOnlyModelView(ModelView):
    def is_accessible(self):
        if not current_user.is_active:
            return False
        if current_app.debug:
            return True
        return current_user.is_admin


class AdminIndex(AdminIndexView):
    @expose("/")
    @login_required
    def index(self):
        return super().index()
