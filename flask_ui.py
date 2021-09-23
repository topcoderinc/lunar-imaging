from flask import Flask, render_template, jsonify, flash, request, redirect, url_for, stream_with_context
#import test
import subprocess
import time, os
from pathlib import Path

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField, TextAreaField, FileField, BooleanField
from wtforms.validators import DataRequired, Length, Email, NumberRange, ValidationError
import helper as h

app = Flask(__name__)
#app.config.from_object('config.Config')
app.config['SECRET_KEY'] = 'secret key is already here'

# OLD_MISSIONS_PATH = '/media/dmitry/SSD/DV/NASA/2021_Topcoder_NASA_FinalRefinement/data_flask/old_missions'
# LROC_MISSION_PATH = '/media/dmitry/SSD/DV/NASA/2021_Topcoder_NASA_FinalRefinement/data_flask/lroc_mission'
# OUTPUT_PATH = '/media/dmitry/SSD/DV/NASA/2021_Topcoder_NASA_FinalRefinement/data_flask/output'
# JUPYTER_ROOT = 'http://localhost:8899/tree'
# COREG_CONFIG = '/media/dmitry/SSD/DV/NASA/2021_Topcoder_NASA_FinalRefinement/code/config.adv'

# OLD_MISSIONS_PATH = '/home/ubuntu/Documents/data_flask/old_missions'
# LROC_MISSION_PATH = '/home/ubuntu/Documents/data_flask/lroc_mission'
# OUTPUT_PATH = '/home/ubuntu/Documents/data_flask/output'
# JUPYTER_ROOT = 'http://localhost:8899/tree'

OLD_MISSIONS_PATH = '/home/ubuntu/Topcoder_FlaskUI/data/old_missions'
LROC_MISSION_PATH = '/home/ubuntu/Topcoder_FlaskUI/data/lroc_mission'
OUTPUT_PATH = '/home/ubuntu/Topcoder_FlaskUI/data/output'
JUPYTER_ROOT = 'http://ec2-3-144-74-167.us-east-2.compute.amazonaws.com:8888/tree'

def range_check(form, field):
    if int(field.data) > 4 or int(field.data) < 1:
        raise ValidationError('Field must be in a range 1..4')


class CoregForm(FlaskForm):
    #print(list(Path(OLD_MISSIONS_PATH).glob('*')))
    dir1 = SelectField('Past Mission folder', [DataRequired()], choices=sorted((Path(OLD_MISSIONS_PATH).glob('*'))))
    dir1_mission = SelectField('Mission', [DataRequired()],
                            choices=[
                                ('lo', 'Lunar orbiter'),
                                ('apollo15', 'Apollo 15'),
                                ('apollo16', 'Apollo 16'),
                                ('apollo17', 'Apollo 17'),
                            ])

    dir1_camera = SelectField('Camera', [DataRequired()],
                            choices=[
                                ('--metric', 'Metric'),
                                ('--panoramic', 'Panoramic'),
                            ])

    dir2 = SelectField('LROC folder', [DataRequired()],
                       choices=sorted([str(s) for s in Path(LROC_MISSION_PATH).glob('*')]))
    dir_output = SelectField('Output folder', [DataRequired()],
                             choices=sorted([str(s) for s in Path(OUTPUT_PATH).glob('*')]))

    coreg_type = SelectField('Co-registration algo:', [DataRequired()],
                            choices=[
                                ('--advanced', 'advanced'),
                                ('--basic', 'basic'),
                            ])
    num_proc = IntegerField('Number of threads',
                            [DataRequired(), NumberRange(1, 4, message="have to be in a range 1..4")], default=4)
    #coreg_config = SelectField('Coreg config', [DataRequired()], choices=sorted([str(s) for s in Path(COREG_CONFIG).glob('*')]))
    #scale = IntegerField('Scale', [DataRequired(), NumberRange(1, 20, message="have to be in a range 1..20")], default=20)
    filter_cn = BooleanField('Control network filtering (advanced co-registration only):', default='checked')
    submit = SubmitField('Submit')


@app.route('/coreglog')
def coreg_log():
    def inner(dir1, dir1_mission, dir1_camera, dir2, dir_output, num_proc, coreg_type, filter_cn):  #, coreg_config, scale):
        """ Redirect output from the CLI tool to the web page """

        if dir1_mission == 'lo':
            mission_key = '--lo'
            mission_type = ''
        else:
            mission_key = '--apollo'
            mission_type = f'--apollo_mission {dir1_mission}'

        if filter_cn == 'True':
            filter_cn = 1
        else:
            filter_cn = 0

        str_exec = f'python -u cli.py ' + \
            f' {mission_key} {dir1} {mission_type} {dir1_camera}' + \
            f' --lro {dir2}' + \
            f' --output_folder {dir_output}' + \
            f' {coreg_type} --num_proc {num_proc}' + \
            f' --filter_cn {filter_cn}'
            #f' --coreg_config {coreg_config}' + \
            #f' --scale {scale}'

        print(f"\nRunning CLI: {str_exec}\n")
        yield f'Command line:<br/> {str_exec.rstrip()} <br/><br/>\n'.encode()

        proc = subprocess.Popen(
            [str_exec],
            shell=True,
            stdout=subprocess.PIPE
        )

        for line in iter(proc.stdout.readline, ''):
            # add the line from CLI tool stdout
            yield line.rstrip() + b'<br/>\n'

            # check if process is still running
            if proc.poll() is not None:
                # process is not running - flush CLI tool stdout and break the loop
                while line:
                   line = proc.stdout.readline()
                   yield line.rstrip() + b'<br/>\n'

                break
            else:
                time.sleep(1)

        # add links to co-reg results directory and the file with statistics
        coreg_url = url_for("coreg")
        jupyter_url = f'{JUPYTER_ROOT}/{Path(dir_output).parts[-2]}/{Path(dir_output).parts[-1]}'
        stats_url = f'{jupyter_url.replace("/tree", "/edit", 1)}/{h.get_stats_filename(h.get_artifacts_prefix(dir1))}'

        href = f"window.location.href='{coreg_url}';"
        html = f'<a href="{jupyter_url}" target="_blank">Co-registration results</a>' + \
               (f'<br/><br/><a href="{stats_url}" target="_blank">Co-registration stats</a>'
                    if coreg_type == '--basic' else '') + \
               f'<br/><br/><button onclick = "{href}">Run again</button>'
        yield html.encode()  # sys.stdout.encoding

    #print(request.args.get('dir1'), request.args.get('dir1_mission'), request.args.get('dir2'), request.args.get('dir_output'))
    #print(request.args.get('num_proc'))
    return app.response_class(stream_with_context(inner(
                                    request.args.get('dir1'),
                                    request.args.get('dir1_mission'),
                                    request.args.get('dir1_camera'),
                                    request.args.get('dir2'),
                                    request.args.get('dir_output'),
                                    request.args.get('num_proc'),
                                    request.args.get('coreg_type'),
                                    request.args.get('filter_cn')
                                    #request.args.get('coreg_config'),
                                    #request.args.get('scale')
    )), mimetype='text/html')


@app.route("/coreg", methods=["GET", "POST"])
def coreg():
    form = CoregForm()
    print(url_for("coreg_log"))
    form.dir1.choices = sorted(Path(OLD_MISSIONS_PATH).glob('*'))
    form.dir2.choices = sorted(Path(LROC_MISSION_PATH).glob('*'))
    form.dir_output.choices = sorted(Path(OUTPUT_PATH).glob('*'))
    #form.coreg_config.choices = sorted(Path(COREG_CONFIG).glob('*'))

    if form.validate_on_submit():
        # run co-registration with chosen params amd show the CLI tool running progress
        return redirect(url_for("coreg_log",
                                dir1=form.dir1.data,
                                dir1_mission=form.dir1_mission.data,
                                dir1_camera=form.dir1_camera.data,
                                dir2=form.dir2.data,
                                dir_output=form.dir_output.data,
                                num_proc=form.num_proc.data,
                                coreg_type=form.coreg_type.data,
                                filter_cn=form.filter_cn.data,
                                #coreg_config=form.coreg_config.data,
                                #scale=form.scale.data
                                ))
    # main form
    return render_template(
        "coreg.html",
        form=form,
        template="form-template",
        jupyter_url=JUPYTER_ROOT
    )

@app.route("/files")
def list_files():
    """Endpoint to list files on the server."""
    files = []
    for filename in os.listdir('.'):
        path = os.path.join('.', filename)
        if os.path.isfile(path):
            files.append(filename)
    return jsonify(files)


#if __name__ == '__main__':
#    app.run(host='0.0.0.0', debug=True)

