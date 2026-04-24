#!/usr/bin/env python3
import pygsheets
import datetime
import json
import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()
logging.basicConfig(level=logging.DEBUG)


@app.post("/json/")
async def handle_json_rpc_json(request: Request):
    logging.debug(f"Path: {request.url.path}")
    logging.debug(f"Method: {request.method}")
    logging.debug("Headers:")
    for header in request.headers:
        logging.debug(f"\t{header}: {request.headers.get(header)}")
    logging.debug("Body:")

    request_json = await request.json()
    if request_json:
        for key, value in request_json.items():
            logging.debug(f"\t{key}: {value}")
    else:
        logging.debug((await request.body()).decode())

    data = dict(request_json)["params"]
    answer = json.loads(data["json"])
    response = {
        "created": (
            datetime.datetime.strptime(answer["created"], "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(hours=3)
        ).strftime("%d.%m.%Y %H:%M:%S")
    }
    answer_data = answer["answer"]["data"]
    for question_key in answer_data:
        # См. раздел README "Типы ответов на вопросы"
        value = answer_data[question_key]["value"]
        question = answer_data[question_key]["question"]
        logging.debug(f"{question} - {value}")
        if question["answer_type"]["slug"] == "answer_files":
            value = "\n".join(f"{i['name']}|{i['path']}" for i in value)
        elif type(value) is list:
            value = "\n".join(t["text"] for t in value)
        response[question_key] = value
    logging.debug("append: ", response)
    table_id = data["table_id"]
    sheet_name = data["sheet_name"]
    start_cell = data.get("start_cell", "A1")
    sort = data.get("sort", "").split(",")

    row_data = sort_row_data(response, sort)
    append_to_table(table_id=table_id, sheet_name=sheet_name, data=row_data, start_cell=start_cell)
    return JSONResponse(content={"message": "OK"}, status_code=200)


def sort_row_data(data: dict[str, str], sort: list[str]) -> list[str]:
    return [data.pop("created") ] + [data.pop(key, "") for key in sort] + list(data.values())


def append_to_table(table_id: str, sheet_name: str, data: list[str], start_cell: str = "A1"):
    gc = pygsheets.authorize(service_file="google_conf.json")
    sh = gc.open_by_key(table_id)

    try:
        sh.worksheets("title", sheet_name)
    except:
        sh.add_worksheet(sheet_name)

    wk_content = sh.worksheet_by_title(sheet_name)
    try:
        wk_content.append_table(values=data, start=start_cell)
    except pygsheets.exceptions.InvalidArgumentValue:
        pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
