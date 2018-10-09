from flask import Flask, render_template, request
from wtforms import Form, TextAreaField, validators
import pandas as pd
import numpy as np
import json
import sys
import os

# Find machine where the app is being run
with open('where.txt') as _f:
    I_am_in = _f.read()

# Get wd where flask is being run
# This is because I'm not installing it just pulling the code
if I_am_in == 'Oakland\n':
    cwd = os.path.abspath(os.path.dirname('app.py'))
    sys.path.append('../DisarmGears/') # Append repo location
elif I_am_in == 'Farringdon\n':
    cwd = os.path.abspath(os.path.dirname('app.py'))
    sys.path.append(cwd + '/DisarmGears/') # Append repo location
else:
    raise ValueError('The location in where.txt is not valid')

from disarm_gears.chain_drives.prototypes import adaptive_prototype_0
from disarm_gears.chain_drives.prototypes import sentinel

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('front_page.html')

# This handles the service for Thailand
@app.route('/bvbd', methods=['POST'])
def bvbd_route():
    if request.method == 'POST':
        json_data = request.get_json()
        json_data = json.loads(json_data)

        # Check data is complete
        assert 'end_date' in json_data.keys(), 'Missing parameter end_date.'
        assert 'data' in json_data.keys(), 'Missing data.'
        assert 'date' in json_data['data'].keys(), 'Mising field date.'
        assert 'lng' in json_data['data'].keys(), 'Mising field lng.'
        assert 'lat' in json_data['data'].keys(), 'Mising field lat.'
        assert 'total_cases' in json_data['data'].keys(), 'Mising field total_cases.'
        assert 'imported_cases' in json_data['data'].keys(), 'Mising field imported_cases.'

        end_date = json_data['end_date']
        dynamic_data = pd.DataFrame(json_data['data'])

        XY_obsv, XY_fore, gam  = sentinel(end_date=end_date, dynamic_data=dynamic_data,
                                          storage_path='storage_bvbd/', obsv_knots=6)

        #original_fields = ['lng', 'lat', 'total_incidence_class', 'exceedance_class', 'total_incidence']
        #output_fields = ['lng', 'lat', 'cat_incidence', 'cat_exceedance', 'incidence']
        original_fields = ['lng', 'lat', 'total_incidence_class', 'total_incidence']
        output_fields = ['lng', 'lat', 'cat_incidence', 'incidence']
        response = {i: XY_fore[j].tolist() for i,j in zip(output_fields, original_fields)}

        return json.dumps(response)

# This handles the NTD service
# TODO change '/post' for '/ntd'
@app.route('/post', methods=['POST'])
def post_route():
    if request.method == 'POST':
        json_data = request.get_json()
        json_data = json.loads(json_data)
        region_data = pd.DataFrame(json_data['region_definition'])
        train_data = pd.DataFrame(json_data['train_data'])

        x_frame = np.array(region_data[['lng', 'lat']])
        x_id = np.array(region_data['id'])
        x_coords = np.array(train_data[['lng', 'lat']])
        n_trials = np.array(train_data['n_trials'])
        n_positive = np.array(train_data['n_positive'])
        threshold = json_data['request_parameters']['threshold']

        response = adaptive_prototype_0(x_frame=x_frame, x_id=x_id,
                                        x_coords=x_coords,
                                        n_positive=n_positive,
                                        n_trials=n_trials,
                                        threshold=threshold,
                                        covariate_layers=None)
        return json.dumps(response)

if __name__ == '__main__':
    app.run()
