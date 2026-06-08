
import sys, requests, constants

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'hello'

@app.route('/move', methods=['GET', 'POST'])
def move():
    response = main_function()
    if response == 201: 
        print("Move completed", file=sys.stderr)
    return "", response

if __name__ == '__main__':
    app.run(debug=True)


def main_function():
    #collect cookido_shopping_list from HA
    response_ha = requests.post(constants.ENDPOINT_HA, data=constants.DATA_HA, headers=constants.HEADERS_HA)
    json_response_ha = response_ha.json()
    dowloaded_shopping_list_ha = json_response_ha["service_response"]["todo.cookidoo_shopping_list"]["items"]

    cookido_shopping_list = []
    for x in dowloaded_shopping_list_ha:
        text = x['description'] + " " + x['summary']
        cookido_shopping_list.append(text)
    
    if cookido_shopping_list == []:
        print("Nothing to move from HA", file=sys.stderr)
        return 500
    else:
        print("Cookido shopping list collected from HA", file=sys.stderr)
    
    #collect mealie_shopping_list_id from MEALIE
    response_mealie = requests.get(constants.ENDPOINT_MEALIE_LISTS, headers=constants.HEADERS_MEALIE)
    json_response_mealie = response_mealie.json()
    
    mealie_shopping_list_id = None
    for x in json_response_mealie["items"]:
        if x["name"] == "shopping":
            mealie_shopping_list_id = x["id"]
            print(f"Mealie shopping list ID: {mealie_shopping_list_id}", file=sys.stderr)

    if mealie_shopping_list_id == None:
        print("Not found list called 'shopping' on mealie", file=sys.stderr)
        return 500
    
    #prepare and POST to MEALIE
    data = []
    for x in cookido_shopping_list:
        temp_dict = {}
        temp_dict = {
            "quantity": 0,
            "note": x,
            "display": x,
            "shoppingListId": mealie_shopping_list_id        
        }
        data.append(temp_dict)
        
    response_mealie = requests.post(constants.ENDPOINT_MEALIE_ITEMS, headers=constants.HEADERS_MEALIE, json=data)
    return response_mealie.status_code

