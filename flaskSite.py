from flask import Flask, request, render_template, flash
from stackapi import StackAPI
import os, glob
import json
import datetime
from operator import itemgetter 
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = 'many random bytes'
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route('/')
def first_form():
    return render_template('FirstSearchForm.html')

def question_frequency(id, site):
    questions = site.fetch('users/{ids}/questions', ids=id)
    popularTags = dict()
    for i in questions['items']:
        for j in i['tags']:
            if j in popularTags:
                popularTags[j] += 1
            else:
                popularTags[j] = 1
    popularTags = dict(sorted(popularTags.items(), key = itemgetter(1), reverse = True)[:5])
    plt.switch_backend('Agg')
    plt.bar(popularTags.keys(), popularTags.values())
    plt.title('Most popular subjects of questions')
    for filename in glob.glob("static/images/popTags_{}*".format(id[0])):
        os.remove(filename) 
    image_name = "popTags_{}_{}.png".format(id[0],datetime.datetime.utcnow().isoformat())
    plt.savefig('static/images/{}'.format(image_name))
    mostRecentQuestion = 0
    for i in questions['items']:
        if mostRecentQuestion < i['creation_date']:
            mostRecentQuestion = i['creation_date']
    return len(questions['items']), datetime.datetime.fromtimestamp(mostRecentQuestion).strftime('%c'), image_name

@app.route('/', methods=['POST'])
def processing_name():
    name = request.form['name']
    site = request.form['site']
    processed_site = site.lower()
    if(processed_site):
        site = StackAPI(processed_site)
    else:
        site = StackAPI("stackoverflow")
    if(request.form['user_id']):
        users = site.fetch('users', ids=[request.form['user_id']])
        questionAmount = question_frequency([request.form['user_id']], site)
        return render_template('SearchResult.html', name = users['items'][0]['display_name'], users = users['items'][0]['display_name'], user_id= users['items'][0]['user_id'],  questions = questionAmount, url='static/images/{}'.format(questionAmount[2]))
    else: 
        processed_name = name
        users = site.fetch('users', inname=processed_name)
        listSameUsers = list()
        listSameUsersID = list()
        for sameUsers in users['items']:
            listSameUsers.append(sameUsers['display_name'])
            listSameUsersID.append(sameUsers['user_id'])
        if(len(listSameUsers) > 1):
            return render_template('SearchResultMany.html', name = processed_name, users = listSameUsers, user_id = listSameUsersID, userAmount = len(users))
        elif(len(listSameUsers) <= 0):
            return render_template('SearchResultNone.html', name = processed_name)
        else:
            questionAmount = question_frequency(listSameUsersID, site)
            return render_template('SearchResult.html', name = processed_name, users = listSameUsers, user_id= listSameUsersID, questions = questionAmount)

if __name__ == '__main__':
    app.run(debug=True)