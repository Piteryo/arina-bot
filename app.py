from flask import Flask, jsonify
from flask import request
import dialogflow
from pydialogflow_fulfillment import DialogflowRequest, DialogflowResponse, SimpleResponse, Suggestions
import requests
import json
import ast
import html2text
import re
from collections import OrderedDict

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False

PROJECT_ID = "small-talk-oqmhuq"

session_client = dialogflow.SessionsClient()
session = session_client.session_path(PROJECT_ID, "123")
language_code = "ru"

base_url = "https://pushkinmuseum.art"

with open("izi.json") as f:
    izi_json = json.load(f)

tour = []
for child in izi_json[0]["content"][0]["children"]:
    if child["location"]["number"].startswith("7."):
        tour.append(child)



@app.route('/event', methods=["GET"])
def welcome():
    event = dialogflow.types.EventInput(name=request.args["text"], language_code=language_code)
    query_input = dialogflow.types.QueryInput(event=event)
    response = session_client.detect_intent(session=session, query_input=query_input)
    return response.query_result.fulfillment_text


def get_tour_stop(step=0):
    stop = tour[step]
    response = requests.get(f"https://api.izi.travel/mtgobjects/{stop['uuid']}?languages=ru", headers={"X-IZI-API-KEY":"f46d3192-3fd1-46ce-9e48-2f32c6a095bf"})
    response = ast.literal_eval(response.text)[0]
    audio_uuid = response["content"][0]["audio"][0]["uuid"]
    image_uuid = response["content"][0]["images"][0]["uuid"]
    audio_url = f"https://media.izi.travel/fae0d384-5475-4134-a0bf-eab6bbf42a1b/{audio_uuid}.m4a"
    stop_image_url = f"https://media.izi.travel/fae0d384-5475-4134-a0bf-eab6bbf42a1b/{image_uuid}_800x600.jpg"
    stop_desc = html2text.html2text(response["content"][0]["desc"])
    title = response["content"][0]["title"]
    return title, stop_desc, stop_image_url, audio_url

@app.route('/', methods=['GET', 'POST'])
def index_page():
    if request.method == 'POST':
        print(request.data)
        dialogflow_request = DialogflowRequest(request.data)

        if 'skills' == dialogflow_request.request_data['queryResult']['intent']['displayName']:
            dialogflow_response = {"fulfillmentText": "Я умею искать события, объекты, запускать экскурсию и многое другое.",
            "fulfillmentMessages": [
                                           {
                                               "card": {
                                                   "title": "Умения",
                                                   "subtitle": "Я умею искать события, объекты, запускать экскурсию и многое другое.",
                                                   "imageUri": '',
                                                   "buttons": [{"text" :"начать экскурсию"}, {"text" :"как добраться до галереи"}, {"text" :"где находится девочка на шаре"}, {"text" :"расскажи о девочке на шаре"}]
                                               }
                                           }]}
            return jsonify(dialogflow_response)

        if 'building_find_context' == dialogflow_request.request_data['queryResult']['intent']['displayName']:
            response = requests.get("http://demo6.charlie.vkhackathon.com:8888/search",
                                    params={"query": dialogflow_request.request_data['queryResult']['outputContexts'][0]['parameters']['building'], "entity": "building"})
            response_dict = ast.literal_eval(response.text)[0]
            if 'source' in dialogflow_request.request_data['originalDetectIntentRequest'].keys():
                dialogflow_response = {"fulfillmentText": response_dict["address"]}
                return jsonify(dialogflow_response)
            else:
                dialogflow_response = {"fulfillmentText": response_dict["address"] + "#"
                                                          + response_dict["coords"] + "#" + base_url + response_dict[
                                                              "img"]}
                return jsonify(dialogflow_response)


        if 'art_objects' in dialogflow_request.get_paramters().keys():
            response = requests.get("http://demo6.charlie.vkhackathon.com:8888/where_is_it",
                                    params={"query": dialogflow_request.get_paramter('art_objects')})
            prom = re.findall('(?<="text":)[^}]*', response.text)
            img_url = re.findall('(?<="img":)[^,]*', response.text)
            if len(img_url) == 0:
                img = ""
            else:
                img = base_url + img_url[-1][1:-1]
            if len(prom) == 0:
                txt = "К сожалению не удалось найти данный экспонат"
            else:
                if 'object_description' == dialogflow_request.request_data['queryResult']['intent']['displayName']:
                    txt = re.sub('"year":.+', "", html2text.html2text(prom[-2][1:-1]))
                else:
                    txt = prom[-1][1:-1]
            if 'source' in dialogflow_request.request_data['originalDetectIntentRequest'].keys():
                dialogflow_response = {"fulfillmentText": txt, "fulfillmentMessages": [
    {
      "card": {
        "title": dialogflow_request.get_paramter('art_objects'),
        "subtitle": txt,
        "imageUri": img
      }
    }
  ]}
                return jsonify(dialogflow_response)
            else:
                dialogflow_response = {"fulfillmentText": txt + "#" + "#" + img}
                return jsonify(dialogflow_response)

            # if 'building_find_context' in dialogflow_request.request_data['queryResult']['intent']['displayName']:

        if len(dialogflow_request.request_data['queryResult']['outputContexts']) > 0:
            if "object" == dialogflow_request.request_data['queryResult']['outputContexts'][0]['name'].split('/')[-1]:
                art_object = dialogflow_request.request_data['queryResult']['outputContexts'][0]['parameters']['art_objects']
                response = requests.get("http://demo6.charlie.vkhackathon.com:8888/where_is_it",
                                        params={"query":art_object})
                prom = re.findall('(?<="text":)[^}]*', response.text)
                img_url = re.findall('(?<="img":)[^,]*', response.text)
                if len(img_url) == 0:
                    img = ""
                else:
                    img = base_url + img_url[-1][1:-1]
                if len(prom) == 0:
                    txt = "К сожалению не удалось найти данный экспонат"
                else:
                    if 'object_description_context' == dialogflow_request.request_data['queryResult']['intent']['displayName']:
                        # = html2text.html2text(prom[-2][1:-1])
                        txt = re.sub('"year":.+', "", html2text.html2text(prom[-2][1:-1]))
                    else:
                        txt = prom[-1][1:-1]
                if 'source' in dialogflow_request.request_data['originalDetectIntentRequest'].keys():
                    dialogflow_response = {"fulfillmentText": txt, "fulfillmentMessages": [
                        {
                            "card": {
                                "title": art_object,
                                "subtitle": txt,
                                "imageUri": img
                            }
                        }
                    ]}
                    return jsonify(dialogflow_response)
                else:
                    dialogflow_response = {"fulfillmentText": txt + "#" + "#" + img}
                    return jsonify(dialogflow_response)


        if 'building' in dialogflow_request.get_paramters().keys():
            response = requests.get("http://demo6.charlie.vkhackathon.com:8888/search",
                                    params={"query": dialogflow_request.get_paramter('building'), "entity": "building"})
            response_dict = ast.literal_eval(response.text)[0]
            if 'source' in dialogflow_request.request_data['originalDetectIntentRequest'].keys():
                dialogflow_response = {"fulfillmentText": response_dict["address"]}
                return jsonify(dialogflow_response)
            else:
                dialogflow_response = {"fulfillmentText": response_dict["address"] + "#"
                + response_dict["coords"] + "#" + base_url + response_dict["img"]}
                return jsonify(dialogflow_response)
                #

        if 'events' in dialogflow_request.get_paramters().keys():
            response = requests.get("http://demo6.charlie.vkhackathon.com:8888/find_event",
                                    params={"query": dialogflow_request.get_paramter('events')})
            prom = re.findall('(?<="text":)[^}]*', response.text)
            if len(prom) == 0:
                txt = "К сожалению не удалось найти данное мероприятие"
            else:
                txt = prom[0]
            if 'source' in dialogflow_request.request_data['originalDetectIntentRequest'].keys():
                dialogflow_response = {"fulfillmentText": txt[1:-1] + "\n Мероприятие пройдет " + re.findall('(?<="date":)[^ ]*', response.text)[0][1:]}
                return jsonify(dialogflow_response)
            else:
                dialogflow_response = {"fulfillmentText": txt[1:-1] + "\n Мероприятие пройдет " + re.findall('(?<="date":)[^ ]*', response.text)[0][1:] + "#" + "#"}
                return jsonify(dialogflow_response)

        if 'audio_guide' in dialogflow_request.request_data['queryResult']['intent']['displayName']:
            if 'audio_guide - next' == dialogflow_request.request_data['queryResult']['intent']['displayName']:
                params = {}
                for cont in dialogflow_request.request_data['queryResult']['outputContexts']:
                    if 'parameters' in cont.keys() and 'cur_step' in cont['parameters'].keys():
                        params = cont['parameters']
                        break
                if not params:
                    step = 0
                    dialogflow_response = {"fulfillmentText": "Кажется что-то пошло не так, перезапустите эскурсию."}
                    return jsonify(dialogflow_response)
                else:
                    step = int(params['cur_step'])
            else:
                step = 0
            if step < len(tour):
                title, stop_desc, stop_image_url, audio_url = get_tour_stop(step)

                dialogflow_response = {"fulfillmentText": stop_desc,
                                       "fulfillmentMessages": [
                                           {
                                               "card": {
                                                   "title": title,
                                                   "subtitle": stop_desc,
                                                   "imageUri": stop_image_url,
                                                   "buttons": [{"text": "далее"}]
                                               }
                                           }],
                                       "outputContexts": [
                {
                  "name": f"{session}/contexts/guide",
                  "lifespanCount": 5,
                  "parameters": {
                    "title": title,
                    "text": stop_desc,
                    "img_url": stop_image_url,
                    "audio_url": audio_url,
                    "cur_step": step+1
                  }
                }
                ]}

                return jsonify(dialogflow_response)
            else:
                dialogflow_response = {"fulfillmentText": "Спасибо за внимание! Экскурсия окончена, приходите к нам еще."}
                return jsonify(dialogflow_response)



        # dialogflow_response.add(
        #     SimpleResponse("СимплРеспонз", "СимплРеспонз2"))
        # #dialogflow_response["fulfillment_text"] = "Фулфиллменттекст"
        # dialogflow_response.add(Suggestions(["About", "Sync", "More info"]))
        # response = app.response_class(response=dialogflow_response.get_final_response(),
        #                               mimetype='application/json')
        return "response"
    else:
        return "505"


@app.route('/text', methods=["GET"])
def text_to_dialogflow():
    text = request.args["text"]
    print(text)
    text_input = dialogflow.types.TextInput(
        text=text, language_code=language_code)

    query_input = dialogflow.types.QueryInput(text=text_input)

    response = session_client.detect_intent(
        session=session, query_input=query_input)

    if response.query_result.intent.display_name == "skills":
        return jsonify(
            [{'response': response.query_result.fulfillment_text, 'coords': "", 'img_url': "", 'audio_url': "", "buttons": ["начать экскурсию", "как добраться до галереи", "где находится девочка на шаре", "расскажи о девочке на шаре"]}])

    if response.query_result.output_contexts and response.query_result.output_contexts[0].name.split('/')[-1] == 'guide':
        title, text, img_url, audio_url = response.query_result.output_contexts[0].parameters.fields['title'].string_value, \
                                          response.query_result.output_contexts[0].parameters.fields[
                                              'text'].string_value,response.query_result.output_contexts[0].parameters.fields['img_url'].string_value,\
                                          response.query_result.output_contexts[0].parameters.fields['audio_url'].string_value,
        return jsonify([{'response': title, 'coords': "", 'img_url': img_url, 'audio_url': ""},
                        {'response': text, 'coords': "", 'img_url': "", 'audio_url': audio_url, "buttons": ["далее"]}])
    print(response.query_result.fulfillment_text)
    if "#" in response.query_result.fulfillment_text:
        response_text, coords, img_link = response.query_result.fulfillment_text.split("#")
    else:
        response_text = response.query_result.fulfillment_text
        coords = ""
        img_link = ""
        audio_url = ""

    coords = coords[3:]
    return jsonify([{'response':response_text, 'coords':coords, 'img_url':img_link, 'audio_url':"", "buttons":[]}])
