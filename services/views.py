# encoding=utf-8

from flask import request, flash, Blueprint, render_template, redirect, url_for, jsonify, current_app as app
from flask_login import login_required, current_user
from flaskweb.app import db
from auth.views import check_user_login
from .models import SurveyInfo, Post, Application, Profile, Idea_Post, Idea_Comments
from .forms import SurveyForm, ProfileForm, IdeaForm
import os
from werkzeug.utils import secure_filename

basedir = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(basedir, "../uploads")
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

bp = Blueprint('main', __name__,
               static_url_path="/static",
               static_folder=os.path.join(basedir, "../static"),
               template_folder=os.path.join(basedir, "../templates"))


@bp.route('/', methods=['GET', 'POST'])
def index():
    # post
    form = SurveyForm()
    if form.validate_on_submit():
        email = form.email.data
        # sent to database
        app.logger.info(email)
        survey = SurveyInfo(email=form.email.data,
                            interests=form.interests.data, year=form.year.data)
        db.session.add(survey)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('index.html', form=form)


# -------------- pricing ----------------------
@bp.route('/pricing', methods=['GET'])
def pricing():
    """
    This route shows the pricing page
    :return:
    """
    return render_template('pricing.html')


# -------------- post ----------------------
@bp.route('/explore', methods=['GET'])
# @login_required
def explore():
    """
    This route shows all posts
    :return:
    """
    page = request.args.get('page', 1, type=int)
    # posts = Post.query.order_by(Post.timestamp.desc()).paginate(
    #     page, app.config['POSTS_PER_PAGE'], False)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, 6, False)
    app.logger.info('Num of posts: ' + str(posts.total))

    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('explore.html', title='Explore',
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


# -------------- post ----------------------
@bp.route('/position_detail/<post_id>', methods=['GET', 'POST'])
# @login_required
def position_detail(post_id):
    """
    This route shows position detail
    :return:
    """
    # get post by post_id
    post = Post.query.filter_by(id=post_id).first_or_404()
    return render_template('post.html', post=post)


# -------------- login ----------------------


# @bp.route('/user')
# @login_required
# def user():
#     return 'hello world %s' % current_user.username


# @bp.route("/api/login", methods=["POST"])
# def login():
#     # rewrite login api
#     data = request.get_json()
#     username = data.get("username")
#     password = data.get("password")
#     if check_user_login(username, password):
#         return redirect(url_for("index"))
#     else:
#         return "login error", 400

# -------------- upload ----------------------

# @login_required
@bp.route('/api/upload', methods=["POST"])
def upload_file():
    """
    Api for uploading resume
    :return: json
    """
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
    file = request.files['file']
    post_id = request.form.to_dict()['post_id']

    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        resume_addr = os.path.join(UPLOAD_FOLDER, filename)
        file.save(resume_addr)
        app.logger.info('Resume saved to ' + resume_addr)

        # save each application to the db
        application = Application(post_id=post_id,
                                  resume_addr=resume_addr)
        db.session.add(application)
        db.session.commit()

        # todo: send email after sending application
        # ref: https://www.twilio.com/blog/2018/03/send-email-programmatically-with-gmail-python-and-flask.html

        # todo: fea/enable download after uploading
        # using restful api
    return jsonify({"code": 0, "fileName": "/api/download/" + file.filename})


def allowed_file(filename):
    """
    If the file is of the acceptable extension
    :param filename: The file name to be checked
    :return:
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# -------------- Profile ----------------------
@bp.route('/profile', methods=["GET", "POST"])
def profile():
    """
    enable this after enable auth
    :return:
    """
    form = ProfileForm()
    if form.validate_on_submit():
        pass
        # user = User(email=form.email.data,
        #             username=form.username.data,
        #             password=pswd,
        #             active=active)
        # db.session.add(user)
        # db.session.commit()
    return render_template('profile.html', form=form)


# -------------- Plaza ----------------------
@bp.route('/plaza', methods=["GET", "POST"])
def plaza():
    """
    This is the feed
    todo: how to design pull/push model???
    todo: how to store it in db?
    pull更好实现？
    :return:
    """
    # receive text inputs
    form = IdeaForm()
    # if form.validate_on_submit():
    # todo: why the validators doesn't work
    if request.method == 'POST':
        app.logger.debug('idea received')
        app.logger.info(form.idea.data)
        idea_post = Idea_Post(body=form.idea.data)
        db.session.add(idea_post)
        db.session.commit()
        flash('Your idea is now live!')
        return redirect(url_for('main.plaza'))
    else:
        app.logger.debug('----GET----')

    page = request.args.get('page', 1, type=int)
    # posts = Post.query.order_by(Post.timestamp.desc()).paginate(
    #     page, app.config['POSTS_PER_PAGE'], False)

    # feeding by timeline
    # paginate object!!!
    idea_posts = Idea_Post.query.order_by(Idea_Post.timestamp.desc()).paginate(
        page, 10, False)
    app.logger.info('Num of idea posts: ' + str(idea_posts.total))

    next_url = url_for('main.plaza', page=idea_posts.next_num) \
        if idea_posts.has_next else None
    prev_url = url_for('main.plaza', page=idea_posts.prev_num) \
        if idea_posts.has_prev else plaza

    return render_template('plaza.html', title='plaza',
                           posts=idea_posts.items, next_url=next_url,
                           prev_url=prev_url, form=form)


# -------------- post ----------------------
@bp.route('/idea_detail/<idea_id>', methods=['GET'])
# @login_required
def idea_detail(idea_id):
    """
    This route shows feed detail
    todo: replies to comments
    :return:
    """
    # get post by idea_id
    idea_post = Idea_Post.query.filter_by(id=idea_id).first_or_404()
    # get comments by idea_id
    comments = Idea_Comments.query.filter_by(id=idea_id).order_by(Idea_Comments.timestamp).all()

    return render_template('idea_post.html', idea_post=idea_post, comments=comments)
