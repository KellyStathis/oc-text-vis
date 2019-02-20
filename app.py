
from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

import requests, math, csv, nltk
from nltk.probability import FreqDist
from nltk import word_tokenize

ocApiUrl = 'https://oc-index.library.ubc.ca'
apiKey = 'ef9544d355f3b5628f771fe6aa2e3ad97265e86a566d876f423b5c961da7cf42'
collection = 'darwin'
perPage = 25
offset = 0

# Query the API for the collection item count
collectionUrl = ocApiUrl + '/collections/' + collection + '?api_key=' + apiKey
apiResponse = requests.get(collectionUrl).json()
itemCount = float(apiResponse['data']['items'])

# Figure out how many pages there are
pages = int(math.ceil(itemCount / float(perPage)))

# Loop through collection item pages to get all items
itemIds = []
for x in range(0, pages):
    collectionItemsUrl = ocApiUrl + '/collections/' + collection
    collectionItemsUrl += '/items?limit=' + str(perPage) + '&offset=' + str(offset) + '&api_key=' + apiKey
    offset += 25
    # Get list of 25 items
    apiResponse = requests.get(collectionItemsUrl).json()
    collectionItems = apiResponse['data']
    # Add each item id to the itemIds list
    for collectionItem in collectionItems:
        itemIds.append(collectionItem['_id'])

items = []
for itemId in itemIds:
    itemUrl = ocApiUrl + '/collections/' + collection + '/items/' + itemId
    apiResponse = requests.get(itemUrl).json()
    item = apiResponse['data']
    itemStore = dict()
    itemStore['id'] = itemId
    itemStore['title'] = item['Title'][0]['value']
    if 'Description' in item:
        itemStore['description'] = item['Description'][0]['value']
    else:
        itemStore['description'] = ''
    if 'FullText' in item:
        itemStore['fullText'] = item['FullText'][0]['value']
    else:
        itemStore['fullText'] = ''
    items.append(itemStore)

def most_common(fullText):
    tokens = word_tokenize(fullText)
    text = nltk.Text(tokens)
    fdist = FreqDist(w.lower() for w in text if w.lower() not in nltk.corpus.stopwords.words('english') and len(w) > 2)
    return fdist.most_common(300)

# Write to CSV
# with open('full-text.csv', 'w') as csvfile:
#     writer = csv.writer(csvfile, delimiter=',')
#     writer.writerow(['ID', 'Title', 'Description', 'Full Text'])
#     for item in items:
#         print(item['title'])
#         writer.writerow([item['id'], item['title'], item['description'], item['fullText']])

@app.route("/")
def hello():
    return render_template("index.html", data=items)

@app.route('/background_process')
def background_process():
    try:
        item_id = request.args.get('item_id', "null", type=str)
        item = next(item for item in items if item["id"]==item_id)
        most_common_words = most_common(item["fullText"])
        return jsonify(mcw=most_common_words,result=item)
    except Exception as e:
        return str(e)
