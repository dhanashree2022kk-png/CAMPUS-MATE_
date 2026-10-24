from __future__ import annotations
import os
from datetime import datetime, date, time, timedelta
from functools import wraps
from pathlib import Path
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / 'instance'
INSTANCE_DIR.mkdir(exist_ok=True)
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('CAMPUSMATE_SECRET_KEY', 'local-development-only-change-me'),
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', f"sqlite:///{(INSTANCE_DIR / 'campusmate.db').as_posix()}"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.environ.get('CAMPUSMATE_HTTPS_ONLY', '0') == '1',
    WTF_CSRF_TIME_LIMIT=None,
    DEBUG=os.environ.get('FLASK_DEBUG', '0') == '1',
)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect(app)
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
CATEGORIES = ['General Announcement', 'Examination', 'Assignment', 'Holiday', 'Event', 'Important Information']
PRIORITIES = ['Low', 'Normal', 'High', 'Urgent']
AUDIENCES = {'all': 'Everyone', 'students': 'Students', 'teachers': 'Teachers', 'staff': 'Faculty and staff'}

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student', index=True)
    student_id = db.Column(db.String(60), unique=True, nullable=True, index=True)
    faculty_id = db.Column(db.String(60), unique=True, nullable=True, index=True)
    course = db.Column(db.String(120))
    department = db.Column(db.String(120))
    semester = db.Column(db.Integer)
    section = db.Column(db.String(20))
    phone = db.Column(db.String(30))
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)
    @property
    def role_label(self): return {'student':'Student','teacher':'Teacher','admin':'Administrator'}.get(self.role, self.role.title())

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='General Announcement', index=True)
    short_description = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default='Normal')
    status = db.Column(db.String(20), nullable=False, default='draft', index=True)
    audience = db.Column(db.String(30), nullable=False, default='all', index=True)
    event_date = db.Column(db.Date)
    expires_at = db.Column(db.Date)
    published_at = db.Column(db.DateTime, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator = db.relationship('User', backref='created_notices', foreign_keys=[created_by])
    @property
    def audience_label(self): return AUDIENCES.get(self.audience, self.audience.title())

class TimetableEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(12), nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    subject_name = db.Column(db.String(140), nullable=False)
    faculty_name = db.Column(db.String(120), nullable=False)
    room_number = db.Column(db.String(60), nullable=False)
    course = db.Column(db.String(120), index=True)
    semester = db.Column(db.Integer, index=True)
    section = db.Column(db.String(20), index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    @property
    def time_label(self): return f'{self.start_time.strftime("%I:%M %p")} – {self.end_time.strftime("%I:%M %p")}'

@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, int(user_id))
    return user if user and user.is_active else None

@app.context_processor
def inject_globals():
    return {'current_year': datetime.now().year, 'today_name': date.today().strftime('%A')}

@app.errorhandler(403)
def forbidden(_): return render_template('error.html', code=403, heading='Access denied', message='This area is restricted to a different CampusMate role.'), 403
@app.errorhandler(404)
def not_found(_): return render_template('error.html', code=404, heading='Page not found', message='The page may have moved or the link may be incorrect.'), 404
@app.errorhandler(500)
def internal_error(_):
    db.session.rollback()
    return render_template('error.html', code=500, heading='Something went wrong', message='CampusMate could not complete that request. Check the terminal if the problem continues.'), 500

def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated: return login_manager.unauthorized()
            if not current_user.is_active or current_user.role not in roles: abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator

def dashboard_for(user):
    return {'student':'student_dashboard','teacher':'teacher_dashboard','admin':'admin_dashboard'}.get(user.role, 'home')
def visible_audiences():
    if current_user.role == 'admin': return list(AUDIENCES)
    if current_user.role == 'student': return ['all','students']
    if current_user.role == 'teacher': return ['all','teachers','staff']
    return ['all']
def parse_date_field(field):
    raw = request.form.get(field, '').strip()
    if not raw: return None
    try: return date.fromisoformat(raw)
    except ValueError: raise ValueError(f'Enter a valid {field.replace("_", " ")}.')
def scoped_timetable(user):
    q = TimetableEntry.query
    if user.role == 'student':
        if user.course: q = q.filter((TimetableEntry.course == user.course) | (TimetableEntry.course.is_(None)) | (TimetableEntry.course == ''))
        if user.semester: q = q.filter((TimetableEntry.semester == user.semester) | (TimetableEntry.semester.is_(None)))
        if user.section: q = q.filter((TimetableEntry.section == user.section) | (TimetableEntry.section.is_(None)) | (TimetableEntry.section == ''))
    elif user.role == 'teacher': q = q.filter_by(faculty_name=user.full_name)
    return q

@app.route('/')
def home():
    if current_user.is_authenticated: return redirect(url_for(dashboard_for(current_user)))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard_for_user():
    return redirect(url_for(dashboard_for(current_user)))

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for(dashboard_for(current_user)))
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower(); password = request.form.get('password','')
        user = User.query.filter_by(email=email).first()
        if user and user.is_active and user.check_password(password):
            login_user(user, remember=request.form.get('remember') == 'on')
            flash(f'Welcome back, {user.full_name.split()[0]}!', 'success')
            # Accept only relative local return targets.
            target = request.args.get('next','')
            if target.startswith('/') and not target.startswith('//'): return redirect(target)
            return redirect(url_for(dashboard_for(user)))
        flash('The email or password is incorrect, or the account is inactive.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for(dashboard_for(current_user)))
    form = request.form if request.method == 'POST' else {}
    if request.method == 'POST':
        name=request.form.get('full_name','').strip(); email=request.form.get('email','').strip().lower(); sid=request.form.get('student_id','').strip(); course=request.form.get('course','').strip(); section=request.form.get('section','').strip().upper(); phone=request.form.get('phone','').strip(); password=request.form.get('password',''); confirm=request.form.get('confirm_password','')
        errors=[]
        if len(name)<2: errors.append('Enter your full name (at least 2 characters).')
        if '@' not in email or '.' not in email.split('@')[-1]: errors.append('Enter a valid email address.')
        if not sid: errors.append('Student ID is required.')
        if not course: errors.append('Course or department is required.')
        try:
            semester=int(request.form.get('semester',''))
            if not 1<=semester<=12: raise ValueError
        except ValueError: semester=None; errors.append('Semester must be a number from 1 to 12.')
        if len(password)<8: errors.append('Password must contain at least 8 characters.')
        if password!=confirm: errors.append('Passwords do not match.')
        if User.query.filter(or_(User.email==email, User.student_id==sid)).first(): errors.append('An account with this email or student ID already exists.')
        if errors:
            for error in errors: flash(error,'error')
            return render_template('register.html', form=form)
        user=User(full_name=name,email=email,student_id=sid,course=course,department=course,semester=semester,section=section or None,phone=phone or None,role='student',is_active=True); user.set_password(password); db.session.add(user); db.session.commit()
        flash('Your CampusMate account has been created. You can now sign in.','success'); return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user(); flash('You have been signed out.','info'); return redirect(url_for('home'))

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method=='POST':
        if request.form.get('action')=='password':
            old=request.form.get('current_password',''); new=request.form.get('new_password',''); confirm=request.form.get('confirm_password','')
            if not current_user.check_password(old): flash('Your current password is incorrect.','error')
            elif len(new)<8: flash('New password must contain at least 8 characters.','error')
            elif new!=confirm: flash('The new passwords do not match.','error')
            else: current_user.set_password(new); db.session.commit(); flash('Your password has been updated.','success')
        else:
            name=request.form.get('full_name','').strip()
            if len(name)<2: flash('Enter a valid full name.','error')
            else: current_user.full_name=name; current_user.phone=request.form.get('phone','').strip() or None; db.session.commit(); flash('Your profile has been updated.','success')
        return redirect(url_for('profile'))
    return render_template('profile.html')

@app.route('/student')
@login_required
@roles_required('student')
def student_dashboard():
    audience=visible_audiences(); q=Notice.query.filter(Notice.status=='published', Notice.audience.in_(audience)); today=date.today(); day=today.strftime('%A')
    classes=scoped_timetable(current_user).filter_by(day_of_week=day).order_by(TimetableEntry.start_time).all()
    notices=q.order_by(Notice.published_at.desc(),Notice.created_at.desc()).limit(5).all()
    events=Notice.query.filter(Notice.status=='published',Notice.category=='Event',Notice.audience.in_(audience),Notice.event_date>=today).order_by(Notice.event_date).limit(4).all()
    return render_template('student_dashboard.html',today_label=day,notice_count=q.count(),today_classes=classes,recent_notices=notices,upcoming_events=events,now_hour=datetime.now().hour,now_date=today.strftime('%d %b %Y'))

@app.route('/teacher')
@login_required
@roles_required('teacher')
def teacher_dashboard():
    day=date.today().strftime('%A'); classes=TimetableEntry.query.filter_by(faculty_name=current_user.full_name,day_of_week=day).order_by(TimetableEntry.start_time).all(); upcoming=TimetableEntry.query.filter_by(faculty_name=current_user.full_name).order_by(TimetableEntry.day_of_week,TimetableEntry.start_time).limit(8).all(); notices=Notice.query.filter(Notice.status=='published',Notice.audience.in_(visible_audiences())).order_by(Notice.published_at.desc()).limit(5).all()
    return render_template('teacher_dashboard.html',today_label=day,today_classes=classes,upcoming_classes=upcoming,recent_notices=notices)

@app.route('/admin')
@login_required
@roles_required('admin')
def admin_dashboard():
    return render_template('admin_dashboard.html',student_count=User.query.filter_by(role='student').count(),teacher_count=User.query.filter_by(role='teacher').count(),notice_count=Notice.query.filter_by(status='published').count(),timetable_count=TimetableEntry.query.count(),latest_notices=Notice.query.order_by(Notice.created_at.desc()).limit(5).all())

@app.route('/admin/users')
@login_required
@roles_required('admin')
def admin_users():
    q=request.args.get('q','').strip(); role=request.args.get('role',''); query=User.query
    if q:
        term=f'%{q}%'; query=query.filter(or_(User.full_name.ilike(term),User.email.ilike(term),User.student_id.ilike(term),User.faculty_id.ilike(term)))
    if role in ('student','teacher','admin'): query=query.filter_by(role=role)
    return render_template('admin_users.html',users=query.order_by(User.created_at.desc()).all(),search=q,role_filter=role)

@app.route('/admin/users/teacher', methods=['POST'])
@login_required
@roles_required('admin')
def create_teacher():
    name=request.form.get('full_name','').strip(); email=request.form.get('email','').strip().lower(); fid=request.form.get('faculty_id','').strip(); dept=request.form.get('department','').strip(); password=request.form.get('password','')
    if len(name)<2 or '@' not in email or not fid or len(password)<8: flash('Enter a name, valid email, faculty ID, and password of at least 8 characters.','error')
    elif User.query.filter(or_(User.email==email,User.faculty_id==fid)).first(): flash('That email or faculty ID is already in use.','error')
    else:
        u=User(full_name=name,email=email,faculty_id=fid,department=dept or None,course=dept or None,role='teacher',is_active=True); u.set_password(password); db.session.add(u); db.session.commit(); flash('Teacher account created successfully.','success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@roles_required('admin')
def toggle_user(user_id):
    user=db.session.get(User,user_id)
    if not user: abort(404)
    if user.id==current_user.id: flash('You cannot deactivate your own account.','error')
    elif user.role=='admin' and user.is_active and User.query.filter_by(role='admin',is_active=True).count()<=1: flash('The last active administrator cannot be deactivated.','error')
    else: user.is_active=not user.is_active; db.session.commit(); flash(f'{user.full_name} is now {"active" if user.is_active else "inactive"}.','success')
    return redirect(url_for('admin_users'))

@app.route('/notices')
@login_required
def notices():
    include_drafts=current_user.role=='admin' and request.args.get('include_drafts')=='1'; query=Notice.query
    if not include_drafts: query=query.filter(Notice.status=='published',Notice.audience.in_(visible_audiences()))
    q=request.args.get('q','').strip(); cat=request.args.get('category','').strip(); sort=request.args.get('sort','newest')
    if q:
        term=f'%{q}%'; query=query.filter(Notice.title.ilike(term)|Notice.content.ilike(term)|Notice.short_description.ilike(term))
    if cat in CATEGORIES: query=query.filter_by(category=cat)
    query=query.order_by(Notice.published_at.asc().nullslast(),Notice.created_at.asc()) if sort=='oldest' else query.order_by(Notice.published_at.desc().nullslast(),Notice.created_at.desc())
    return render_template('notices.html',notices=query.all(),categories=CATEGORIES,search=q,category_filter=cat,sort=sort,include_drafts=include_drafts)

@app.route('/notices/<int:notice_id>')
@login_required
def notice_detail(notice_id):
    notice=db.session.get(Notice,notice_id)
    if not notice: abort(404)
    if current_user.role!='admin' and (notice.status!='published' or notice.audience not in visible_audiences()): abort(404)
    return render_template('notice_detail.html',notice=notice)

@app.route('/notices/create', methods=['GET','POST'])
@login_required
@roles_required('admin')
def notice_create():
    return handle_notice_form(None)

@app.route('/notices/<int:notice_id>/edit', methods=['GET','POST'])
@login_required
@roles_required('admin')
def notice_edit(notice_id):
    notice=db.session.get(Notice,notice_id)
    if not notice: abort(404)
    return handle_notice_form(notice)

def handle_notice_form(existing):
    if request.method=='POST':
        title=request.form.get('title','').strip(); short=request.form.get('short_description','').strip(); content=request.form.get('content','').strip(); category=request.form.get('category',''); priority=request.form.get('priority','Normal'); status=request.form.get('status','draft'); audience=request.form.get('audience','all')
        try: event_date=parse_date_field('event_date'); expires_at=parse_date_field('expires_at')
        except ValueError as exc: flash(str(exc),'error'); return render_template('notice_form.html',notice=existing,categories=CATEGORIES,priorities=PRIORITIES,audiences=AUDIENCES,form=request.form)
        error=None
        if not title or not short or not content: error='Title, short description, and full content are required.'
        elif category not in CATEGORIES or priority not in PRIORITIES or status not in ('draft','published') or audience not in AUDIENCES: error='Choose valid category, priority, publication status, and audience options.'
        elif event_date and expires_at and expires_at<event_date: error='Expiry date cannot be earlier than the event date.'
        if error: flash(error,'error'); return render_template('notice_form.html',notice=existing,categories=CATEGORIES,priorities=PRIORITIES,audiences=AUDIENCES,form=request.form)
        n=existing or Notice(created_by=current_user.id); was_published=bool(existing and existing.status=='published')
        n.title=title; n.short_description=short; n.content=content; n.category=category; n.priority=priority; n.status=status; n.audience=audience; n.event_date=event_date; n.expires_at=expires_at
        if status=='published' and (not was_published or not n.published_at): n.published_at=datetime.utcnow()
        elif status=='draft': n.published_at=None
        db.session.add(n); db.session.commit(); flash('Notice saved successfully.','success'); return redirect(url_for('notices',include_drafts='1'))
    return render_template('notice_form.html',notice=existing,categories=CATEGORIES,priorities=PRIORITIES,audiences=AUDIENCES,form={})

@app.route('/notices/<int:notice_id>/delete', methods=['POST'])
@login_required
@roles_required('admin')
def notice_delete(notice_id):
    n=db.session.get(Notice,notice_id)
    if not n: abort(404)
    db.session.delete(n); db.session.commit(); flash('Notice deleted.','success'); return redirect(url_for('notices',include_drafts='1'))

@app.route('/timetable')
@login_required
def timetable():
    view=request.args.get('view','week'); selected=request.args.get('day',date.today().strftime('%A'))
    if selected not in DAYS: selected=date.today().strftime('%A')
    query=scoped_timetable(current_user)
    if view=='day': query=query.filter_by(day_of_week=selected)
    entries=query.order_by(TimetableEntry.day_of_week,TimetableEntry.start_time).all()
    grouped={selected:entries} if view=='day' else {day:[e for e in entries if e.day_of_week==day] for day in DAYS}
    return render_template('timetable.html',entries=entries,grouped=grouped,days=DAYS,selected_day=selected,view=view,can_manage=current_user.role=='admin')

@app.route('/timetable/create', methods=['GET','POST'])
@login_required
@roles_required('admin')
def timetable_create(): return handle_timetable_form(None)

@app.route('/timetable/<int:entry_id>/edit', methods=['GET','POST'])
@login_required
@roles_required('admin')
def timetable_edit(entry_id):
    entry=db.session.get(TimetableEntry,entry_id)
    if not entry: abort(404)
    return handle_timetable_form(entry)

def handle_timetable_form(existing):
    if request.method=='POST':
        day=request.form.get('day_of_week',''); subject=request.form.get('subject_name','').strip(); faculty=request.form.get('faculty_name','').strip(); room=request.form.get('room_number','').strip(); course=request.form.get('course','').strip(); section=request.form.get('section','').strip().upper(); sem_raw=request.form.get('semester','').strip()
        try: start=time.fromisoformat(request.form.get('start_time','')); end=time.fromisoformat(request.form.get('end_time',''))
        except ValueError: flash('Enter valid start and end times.','error'); return render_template('timetable_form.html',entry=existing,days=DAYS,form=request.form)
        try:
            semester=int(sem_raw) if sem_raw else None
            if semester is not None and not 1<=semester<=12: raise ValueError
        except ValueError: flash('Semester must be a number from 1 to 12.','error'); return render_template('timetable_form.html',entry=existing,days=DAYS,form=request.form)
        error=None
        if day not in DAYS or not subject or not faculty or not room: error='Day, subject, faculty name, and classroom are required.'
        elif end<=start: error='End time must be later than start time.'
        if not error:
            conflicts=TimetableEntry.query.filter(TimetableEntry.day_of_week==day,TimetableEntry.start_time<end,TimetableEntry.end_time>start)
            if existing: conflicts=conflicts.filter(TimetableEntry.id!=existing.id)
            for other in conflicts.all():
                same_room=room.casefold()==other.room_number.casefold(); same_faculty=faculty.casefold()==other.faculty_name.casefold(); same_group=bool(course and semester and section and other.course and other.semester and other.section and course.casefold()==other.course.casefold() and semester==other.semester and section==other.section)
                if same_room or same_faculty or same_group:
                    conflict='classroom' if same_room else ('faculty member' if same_faculty else 'student group'); error=f'This time overlaps an existing class for the same {conflict}. Choose another time or resource.'; break
        if error: flash(error,'error'); return render_template('timetable_form.html',entry=existing,days=DAYS,form=request.form)
        e=existing or TimetableEntry(); e.day_of_week=day; e.start_time=start; e.end_time=end; e.subject_name=subject; e.faculty_name=faculty; e.room_number=room; e.course=course or None; e.semester=semester; e.section=section or None; db.session.add(e); db.session.commit(); flash('Timetable entry saved.','success'); return redirect(url_for('timetable',view='week'))
    return render_template('timetable_form.html',entry=existing,days=DAYS,form={})

@app.route('/timetable/<int:entry_id>/delete', methods=['POST'])
@login_required
@roles_required('admin')
def timetable_delete(entry_id):
    e=db.session.get(TimetableEntry,entry_id)
    if not e: abort(404)
    db.session.delete(e); db.session.commit(); flash('Timetable entry deleted.','success'); return redirect(url_for('timetable',view='week'))

@app.cli.command('init-db')
def init_db_command():
    """Create tables, preserving existing data."""
    with app.app_context(): db.create_all()
    print('CampusMate database tables are ready.')

if __name__=='__main__':
    with app.app_context(): db.create_all()
    print('\nCampusMate is running at http://127.0.0.1:5000')
    app.run(host='127.0.0.1',port=int(os.environ.get('PORT','5000')),debug=app.config['DEBUG'])
