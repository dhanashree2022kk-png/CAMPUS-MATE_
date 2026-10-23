"""Populate fictional local demo data. Do not use demo credentials in production."""
import os
from datetime import datetime, date, time, timedelta
from app import app, db, User, Notice, TimetableEntry

password = os.environ.get('CAMPUSMATE_DEMO_PASSWORD', 'CampusDemo123!')
with app.app_context():
    db.create_all()
    def user(email, name, role, **fields):
        value = User.query.filter_by(email=email).first()
        if value: return value
        value = User(email=email, full_name=name, role=role, is_active=True, **fields)
        value.set_password(password); db.session.add(value); db.session.flush(); return value
    admin = user('admin@campusmate.local','Campus Administrator','admin',department='Administration')
    user('teacher@campusmate.local','Aarav Sharma','teacher',faculty_id='FAC-1001',department='Computer Applications',course='Computer Applications')
    user('student@campusmate.local','Ananya Patil','student',student_id='CM-2026-001',course='BCA',department='Computer Applications',semester=3,section='A',phone='9000000000')
    if Notice.query.count() == 0:
        db.session.add_all([
            Notice(title='Mid-Semester Examination Schedule',category='Examination',short_description='The mid-semester examination schedule is available for students.',content='Please check the timetable and reach your examination room at least 15 minutes before the start time. Carry your college identity card.',priority='High',status='published',audience='students',published_at=datetime.utcnow(),created_by=admin.id),
            Notice(title='Assignment Submission Reminder',category='Assignment',short_description='Submit pending assignments through the prescribed faculty process.',content='Review your course requirements and contact the relevant faculty member if you need clarification.',priority='Normal',status='published',audience='students',published_at=datetime.utcnow()-timedelta(hours=4),created_by=admin.id),
            Notice(title='Campus Cleanliness Drive',category='Event',short_description='Join campus volunteers for a cleanliness and awareness drive.',content='Volunteers are welcome. Meet the student coordination team near the main courtyard.',priority='Normal',status='published',audience='all',event_date=date.today()+timedelta(days=5),published_at=datetime.utcnow(),created_by=admin.id),
            Notice(title='Library Holiday Hours',category='Holiday',short_description='The library will follow revised hours on the announced date.',content='Check with the library counter for updates before planning a visit.',priority='Low',status='published',audience='all',published_at=datetime.utcnow()-timedelta(days=1),created_by=admin.id),
            Notice(title='Draft: Faculty Meeting',category='Important Information',short_description='Draft notice visible only to administrators.',content='Confirm the date and agenda before publishing this notice.',priority='Normal',status='draft',audience='teachers',created_by=admin.id),
        ])
    if TimetableEntry.query.count() == 0:
        demo = [
            ('Monday',time(9),time(10),'Database Management Systems','Aarav Sharma','Room 204','BCA',3,'A'),
            ('Monday',time(10,15),time(11,15),'Web Development','Aarav Sharma','Lab 2','BCA',3,'A'),
            ('Tuesday',time(9),time(10),'Python Programming','Aarav Sharma','Lab 1','BCA',3,'A'),
            ('Wednesday',time(11),time(12),'Software Engineering','Aarav Sharma','Room 205','BCA',3,'A'),
            ('Thursday',time(10),time(11),'Database Management Systems','Aarav Sharma','Room 204','BCA',3,'A'),
            ('Friday',time(12),time(13),'Project Lab','Aarav Sharma','Lab 2','BCA',3,'A'),
        ]
        for day,start,end,subject,faculty,room,course,semester,section in demo:
            db.session.add(TimetableEntry(day_of_week=day,start_time=start,end_time=end,subject_name=subject,faculty_name=faculty,room_number=room,course=course,semester=semester,section=section))
    db.session.commit()
print('Demo data ready. Password for seeded accounts:', password)
print('Administrator: admin@campusmate.local')
print('Teacher:       teacher@campusmate.local')
print('Student:       student@campusmate.local')
