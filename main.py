import logging

from flask import Flask, jsonify
from flask import has_request_context, request
from flask.logging import default_handler
from markupsafe import escape

from algo.asset import Asset
from algo.setup import getAlgodClient, getOfficialAccount
from algo.util import createAsset


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None

        return super().format(record)

formatter = RequestFormatter(
    '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
    '%(levelname)s in %(module)s: %(message)s'
)
default_handler.setFormatter(formatter)

app = Flask(__name__)


@app.route("/mintAsa", methods=['POST'])
def mint_asa():
    # 1. 获取链接
    client = getAlgodClient()
    # 2. 组装asa对象
    asa_name = request.json.get('asaName')
    asa_unit = request.json.get('asaUnit')
    asa_url = request.json.get('asaUrl')
    asa_total = int(request.json.get('asaTotal'))

    asset = Asset(asa_unit, asa_name, asa_url, asa_total)
    logging.info(f"mint asa metadata:{asset},minting....")

    # 3. mint 资产
    officialAccount = getOfficialAccount()
    asaIndex = createAsset(client, asset, officialAccount)

    if (asaIndex):
        response = {
            'result': '01',
            'resultCode': '000000',
            'resultMessage': 'Mint资产成功',
            'asaId': asaIndex
        }
    else:
        response = {
            'result': '02',
            'resultCode': '000000',
            'resultMessage': 'Mint资产失败'
        }
    return jsonify(response)

@app.route("/deployContract", methods=['POST'])
def deploy_contract():
    asaName = request.json.get('asaName')
    response = {
        'result': '01',
        'asaId': '100001'
    }
    return jsonify(response)

# 转义，防止注入攻击
@app.route("/<name>")
def hello(name):
    return f"Hello, {escape(name)}"
