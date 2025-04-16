#!/usr/bin/env python3

from flask import Flask, request, jsonify
import pygsheets
import datetime
import json
import logging


app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)


@app.route('/json/', methods=['POST'])
def handle_json_rpc_json():
    logging.debug(f'Path: {request.path}')
    logging.debug(f'Method: {request.method}')
    logging.debug('Headers:')
    for header in request.headers:
        logging.debug(f'\t{header}: {request.headers.get(header)}')
    logging.debug('Body:')
    if request.json:
        for key, value in request.json.items():
            logging.debug(f'\t{key}: {value}')
    else:
        logging.debug(request.data.decode())

    data = dict(request.json)['params']
    answer = json.loads(data['json'])
    response = {'created': (datetime.datetime.strptime(answer['created'], "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(hours=3)).strftime("%d.%m.%Y %H:%M:%S")}
    answer_data = answer['answer']['data']
    for question_key in answer_data:
        # См. раздел README "Типы ответов на вопросы"
        value = answer_data[question_key]['value']
        question = answer_data[question_key]['question']
        logging.debug(f"{question} - {value}")
        if question['answer_type']['slug'] == 'answer_files':
            value = '\n'.join(f"{i['name']}|{i['path']}" for i in value)
        elif type(value) is list:
            value = "\n".join(t['text'] for t in value)
        response[question_key] = value
    logging.debug("append: ", response)
    table_id = data['table_id']
    sheet_name = data['sheet_name']
    append_to_table(table_id, sheet_name, response)

    return jsonify({'message': 'OK'}), 200


@app.route('/', methods=['POST'])
def handle_json_rpc():
    # DEPRECATED
    response_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    response = {'response_time': response_time}
    print(f'Path: {request.path}')
    print(f'Method: {request.method}')
    print('Headers:')
    for header in request.headers:
        print(f'\t{header}: {request.headers.get(header)}')
    print('Body:')
    if request.json:
        for key, value in request.json.items():
            print(f'\t{key}: {value}')
    else:
        print(request.data.decode())

    response.update(dict(request.json)['params'])
    table_id = response.pop('table_id')
    sheet_name = response.pop('sheet_name')
    print("append: ", response)
    append_to_table(table_id, sheet_name, response)

    return jsonify({'message': 'OK'}), 200


def append_to_table(table_id, sheet_name, data):
    gc = pygsheets.authorize(service_file="google_conf.json")
    sh = gc.open_by_key(table_id)

    try:
        sh.worksheets('title', sheet_name)
    except:
        sh.add_worksheet(sheet_name)

    wk_content = sh.worksheet_by_title(sheet_name)
    try:
        wk_content.append_table(values=list(data.values()))
    except pygsheets.exceptions.InvalidArgumentValue:
        pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8010, debug=True)
