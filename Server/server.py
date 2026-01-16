from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dbFuncs import *

server = Flask(__name__, static_url_path='', static_folder='../Client')
CORS(server)

###############
# Page Routes #
###############

@server.route('/', methods=['GET', 'POST'])
def index():
    return server.send_static_file('HTML/index.html')

##############
# API Routes #
##############

@ server.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "pong"})

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5000, debug=True)