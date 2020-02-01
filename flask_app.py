from flask_bootstrap import Bootstrap
from flask import request, send_file, render_template, Flask
import subprocess, os, io, shutil, yaml, pickle
from datetime import datetime

APP_DIR = os.getcwd()
JOB_DIR = APP_DIR + '/job'
DOWNLOAD_DIR = APP_DIR + '/download'
HTML_DIR = JOB_DIR + '/html'
TXT_DIR = JOB_DIR + '/txt'
TMP_DIR = JOB_DIR + '/tmp'

ALLOWED_EXTENSIONS = set(['txt'])

global config

app = Flask(__name__)
bootstrap = Bootstrap(app)


app.config["DEBUG"] = False

app.config['JOB_DIR'] = JOB_DIR
app.config['DOWNLOAD_DIR'] = DOWNLOAD_DIR
app.config['HTML_DIR'] = HTML_DIR
app.config['TXT_DIR'] = TXT_DIR
app.config['TMP_DIR'] = TMP_DIR

app.secret_key = "TvF8WJlOIdaAUkeeCxjsJem3X3gHRN8T"

# ===========
# FUNCTIONS
# ===========

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def reset_files():
    shutil.rmtree(app.config['JOB_DIR'], ignore_errors=True)
    shutil.rmtree(app.config['DOWNLOAD_DIR'], ignore_errors=True)
    os.makedirs(app.config['JOB_DIR'])
    os.makedirs(app.config['DOWNLOAD_DIR'])
    os.makedirs(app.config['HTML_DIR'])
    os.makedirs(app.config['TXT_DIR'])
    os.makedirs(app.config['TMP_DIR'])
    with open(app.config['TMP_DIR'] + "/" + "session_log.txt", "w") as out:
        out.write(cfg['msg']['session_log_default'])
    with open(app.config['TMP_DIR'] + "/" + "download_msg.txt", "w") as out:
        out.write(cfg['msg']['download_msg_default'])

def load_config(file):
    with open(file, 'r') as stream:
        config_defaults = yaml.safe_load(stream)
    return config_defaults

def messaging():
    settings = pickle.load(open(app.config['TMP_DIR'] + '/settings.txt', "rb"))
    print(settings['exit'])
    if settings['exit'] > 0:
        with open(app.config['TMP_DIR'] + "/" + "session_log.txt", "a") as out:
            out.write(cfg['msg']['session_log_complete'])
        with open(app.config['TMP_DIR'] + "/" + "download_msg.txt", "w") as out:
            out.write(cfg['msg']['download_msg_complete'])
            out.write(cfg['msg']['download_msg_url'] + this_name + ".zip" + cfg['msg']['download_msg_url_archive'])
    elif settings['exit'] == 0:
        with open(app.config['TMP_DIR'] + "/" + "session_log.txt", "a") as out:
            out.write(cfg['msg']['session_log_error'])
        with open(app.config['TMP_DIR'] + "/" + "download_msg.txt", "w") as out:
            out.write(cfg['msg']['download_msg_error'])
            out.write(cfg['msg']['start_again_button'])
    else:
        with open(app.config['TMP_DIR'] + "/" + "session_log.txt", "a") as out:
            out.write(cfg['msg']['session_log_fatal'])
        with open(app.config['TMP_DIR'] + "/" + "download_msg.txt", "w") as out:
            out.write(cfg['msg']['download_msg_fatal'])
            out.write(cfg['msg']['start_again_button'])

def upload():
    file = request.files['file']
    year = request.form['year']
    global base_url
    if year == "":
        base_url = "https://programsandcourses.anu.edu.au/course/"
    else:
        base_url = "https://programsandcourses.anu.edu.au/" + year + "/course/"

    if file:
        if allowed_file(file.filename):
            file_dir = os.path.join(app.config['JOB_DIR'], 'codes.txt')
            file.save(file_dir)
            return ('', 205)
        else:
            return render_template('error.html')

def cleaner():
    global this_name
    now = datetime.now()
    this_name = now.strftime("%Y%m%d%H%M%S")
    shutil.make_archive(app.config['DOWNLOAD_DIR'] + "/" + this_name, 'zip', app.config['JOB_DIR'])
    shutil.rmtree(app.config['HTML_DIR'], ignore_errors=True)
    shutil.rmtree(app.config['TXT_DIR'], ignore_errors=True)

def processing():
    this_file = os.path.join(app.config['JOB_DIR'], 'codes.txt')
    print(this_file)
    print(base_url)
    subprocess.call("python3 pace.py " + this_file + " " + base_url, shell=True)


# ===========
# VIEWS
# ===========

@app.route('/', methods=['GET', 'POST'])
def index():
    reset_files()
    if request.method == 'POST':
        upload()
        processing()
        cleaner()
        messaging()
        return ('', 205)
    return render_template('index.html')


@app.route('/console_msg')
def console_msg():
    def generate():
        with open(app.config['TMP_DIR'] + '/session_log.txt') as f:
            while True:
                content = f.read()
                return content
    return app.response_class(generate(), mimetype='text/plain')

@app.route('/download_msg')
def download_msg():
    def generate_msg():
        with open(app.config['TMP_DIR'] + '/download_msg.txt') as f:
            while True:
                content = f.read()
                return content
    return app.response_class(generate_msg(), mimetype='text/plain')

@app.route('/error')
def error():
    return render_template('error.html')

@app.route('/download_file/<filename>')
def download_remove_file(filename):
    file_path = os.path.join(app.config['DOWNLOAD_DIR'], filename)
    return_data = io.BytesIO()
    with open(file_path, 'rb') as file_out:
        return_data.write(file_out.read())
    return_data.seek(0)
    os.remove(file_path)
    return send_file(
        return_data,
        mimetype='application/pdf',
        as_attachment=True,
        attachment_filename=filename)

@app.route('/download_archive/<filename>')
def download_remove_archive(filename):
    path = os.path.join(app.config['DOWNLOAD_DIR'], filename)
    def generate():
        with open(path) as f:
            yield from f
        os.remove(path)
    r = app.response_class(generate(), mimetype='applicationa/zip')
    r.headers.set('Content-Disposition', 'attachment', filename=filename)
    return r

cfg = load_config("./includes/yml/messages.yml")

if __name__ == '__main__':
    # app.run()
    app.run()
