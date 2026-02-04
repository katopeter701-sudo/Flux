from flask import Flask, render_template_string, request, redirect, url_for, session
from supabase import create_client
import pandas as pd
import re
import os

app = Flask(__name__)
app.secret_key = "flux_secret_key_123" # Change this for security

# 1. DATABASE CONNECTION
SUPABASE_URL = "https://uxtmgdenwfyuwhezcleh.supabase.co"
SUPABASE_KEY = "sb_publishable_1BIwMEH8FVDv7fFafz31uA_9FqAJr0-" 
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# HELPER: Drive Link Converter
def convert_drive_url(url):
    if "drive.google.com" in url:
        match = re.search(r'[-\w]{25,}', url)
        if match: return f"https://drive.google.com/uc?id={match.group()}"
    return url

# 2. THE DESIGN (CSS)
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Flux Portal</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Comic+Neue:wght@700&display=swap');
        body { font-family: 'Comic Neue', cursive; background: #f4f7f6; margin: 0; padding: 20px; }
        .nav { background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .nav a { margin-right: 20px; text-decoration: none; color: #333; font-weight: bold; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
        .card { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); transition: 0.3s; }
        .card:hover { transform: translateY(-5px); }
        .card img { width: 100%; height: 180px; object-fit: cover; }
        .card-body { padding: 15px; text-align: center; }
        input, button { padding: 10px; margin: 5px 0; width: 100%; border-radius: 5px; border: 1px solid #ddd; }
        button { background: #333; color: white; cursor: pointer; border: none; }
        button:hover { background: #555; }
        .container { max-width: 1000px; margin: auto; }
    </style>
</head>
<body>
    <div class="nav">
        <strong>Flux</strong> | 
        <a href="/">Home</a>
        <a href="/admin">Admin</a>
        {% if session.get('user') %} <span style="float:right">Hi, {{ session['user'] }}</span> {% endif %}
    </div>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

# 3. ROUTES (THE PAGES)
@app.route('/')
def home():
    res = supabase.table("materials").select("course_program, image_url").execute()
    courses = {item['course_program']: item['image_url'] for item in res.data} if res.data else {}
    
    html = """
    {% extends "base" %}
    {% block content %}
    <h1 style="text-align:center">Explore Courses</h1>
    <div class="grid">
        {% for name, img in courses.items() %}
        <div class="card">
            <img src="{{ img if img else 'https://via.placeholder.com/300' }}">
            <div class="card-body">
                <h3>{{ name }}</h3>
                <a href="/course/{{ name }}"><button>Open Course</button></a>
            </div>
        </div>
        {% endfor %}
    </div>
    {% endblock %}
    """
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', html), courses=courses)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        pw = request.form.get('pw')
        if pw == "flux":
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', '<h2>Admin Login</h2><form method="POST"><input type="password" name="pw" placeholder="Enter Admin Password"><button type="submit">Login</button></form>'))

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('is_admin'): return redirect(url_for('admin'))
    
    if request.method == 'POST':
        c_name = request.form.get('c_name')
        drive_url = convert_drive_url(request.form.get('drive_url'))
        file = request.files.get('file')
        if file:
            df = pd.read_excel(file) if file.filename.endswith('xlsx') else pd.read_csv(file)
            for idx, row in df.iterrows():
                supabase.table("materials").insert({
                    "course_program": c_name,
                    "course_name": str(row.get('Topic Covered', f'Mod {idx+1}')),
                    "week": idx + 1,
                    "video_url": str(row.get('Embeddable YouTube Video Link', '')),
                    "notes_url": str(row.get('link to Google docs Document', '')),
                    "image_url": drive_url
                }).execute()
            return "Course Uploaded Successfully! <a href='/admin/dashboard'>Back</a>"

    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', '<h2>Create New Course</h2><form method="POST" enctype="multipart/form-data"><input name="c_name" placeholder="Course Name"><input name="drive_url" placeholder="Google Drive Image URL"><input type="file" name="file"><button type="submit">Deploy Course</button></form>'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
