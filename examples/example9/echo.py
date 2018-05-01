#!/usr/bin/env python2

import time

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/echo', methods=['POST'])
def echo():
    time.sleep(0.2)
    return jsonify(request.json)


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
