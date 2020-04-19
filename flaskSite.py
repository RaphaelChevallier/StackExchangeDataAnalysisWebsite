from flask import Flask, request, render_template, flash
from stackapi import StackAPI
import os, glob
import json
import time
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
    topAnswersTags = site.fetch('users/{ids}/top-answer-tags', ids=id)
    topTagsAnswered = dict()
    print(topAnswersTags['items'])
    for answerTags in topAnswersTags['items']:
        if answerTags['tag_name'] not in topTagsAnswered:
            topTagsAnswered[answerTags['tag_name']] = 1
        else:
            topTagsAnswered[answerTags['tag_name']] +=1
    topTagsAnswered = dict(sorted(topTagsAnswered.items(), key = itemgetter(1), reverse = True)[:5])
    popularTags = dict()
    for i in questions['items']:
        for j in i['tags']:
            if j in popularTags:
                popularTags[j] += 1
            else:
                popularTags[j] = 1
    popularTags = dict(sorted(popularTags.items(), key = itemgetter(1), reverse = True)[:5])
    plt.switch_backend('Agg')
    plt.figure(0)
    plt.bar(popularTags.keys(), popularTags.values())
    plt.title('Most popular tags user asked questions too')
    plt.xlabel("Tags")
    plt.ylabel("Amount of Questions Answered")
    for filename in glob.glob("static/images/*"):
        if filename is None:
            continue
        else:
            os.remove(filename) 
    image_name = "popTags_{}_{}.png".format(id[0],datetime.datetime.utcnow().isoformat())
    plt.savefig('static/images/{}'.format(image_name))
    plt.figure(1)
    plt.bar(topTagsAnswered.keys(), topTagsAnswered.values())
    plt.title('Most popular tags user answered questions too')
    plt.xlabel("Tags")
    plt.ylabel("Amount of Tags")
    image_name2 = "popAnsweredTags_{}_{}.png".format(id[0],datetime.datetime.utcnow().isoformat())
    plt.savefig('static/images/{}'.format(image_name2))
    mostRecentQuestion = 0
    for i in questions['items']:
        if mostRecentQuestion < i['creation_date']:
            mostRecentQuestion = i['creation_date']
    return len(questions['items']), datetime.datetime.fromtimestamp(mostRecentQuestion).strftime('%c'), image_name, image_name2

def posting_frequency(id, site, createdUserDate, totalQuestions):
    posts = site.fetch('users/{ids}/posts', ids=id, order='asc', sort='creation')
    frequency_graph = dict()
    for post in posts['items']:
        humanTime = time.strftime('%m-%Y', time.localtime(post['creation_date']))
        if humanTime not in frequency_graph:
            frequency_graph[humanTime] = 1
        else:
            frequency_graph[humanTime] +=1
    plt.switch_backend('Agg')
    plt.bar(frequency_graph.keys(), frequency_graph.values())
    plt.title('Posting frequency by active months')
    plt.xlabel("Months")
    plt.ylabel("Amount of Posts")
    image_name = "postFrequency_{}_{}.png".format(id[0],datetime.datetime.utcnow().isoformat())
    plt.savefig('static/images/{}'.format(image_name))
    return image_name

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
        createdUserDate = users['items'][0]['creation_date']
        questionAmount = question_frequency([request.form['user_id']], site)
        post_frequency = posting_frequency([request.form['user_id']], site, createdUserDate, questionAmount[0])
        return render_template('SearchResult.html', name = users['items'][0]['display_name'], users = users['items'][0]['display_name'], user_id= users['items'][0]['user_id'],  questions = questionAmount, question_url='static/images/{}'.format(questionAmount[2]), answerTags_url='static/images/{}'.format(questionAmount[3]), posting_url='static/images/{}'.format(post_frequency))
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
            createdUserDate = listSameUsers[0]['items'][0]['creation_date']
            post_frequency = posting_frequency([request.form['user_id']], site, createdUserDate, questionAmount[0])
            return render_template('SearchResult.html', name = processed_name, users = listSameUsers, user_id= listSameUsersID, questions = questionAmount, question_url='static/images/{}'.format(questionAmount[2]), answerTags_url='static/images/{}'.format(questionAmount[3]), posting_url='static/images/{}'.format(post_frequency))

if __name__ == '__main__':
    app.run(debug=True)