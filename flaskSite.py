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

def timeline(id,site):
    timeline = site.fetch('users/{ids}/timeline', ids=id, fromdate=(datetime.date.today() + datetime.timedelta(6*365/12)).isoformat())
    dates = dict()
    for date in timeline['items']:
        dates[time.strftime('%m-%Y', time.localtime(date['creation_date']))]  = date['post_type']
    plt.switch_backend('Agg')
    plt.plot_date(dates.keys(), dates.values())
    plt.title('Recent 6 Months Timeline of Activity')
    plt.xlabel("Dates")
    plt.ylabel("Question Type")
    image_name = "timeline{}_{}.png".format(id[0],datetime.datetime.utcnow().isoformat())
    plt.savefig('static/images/{}'.format(image_name))
    return image_name

def tag_help(id, site, tag):
    tagHelp = site.fetch('tags/{tag}/top-answerers/month', tag=tag)
    return tagHelp['items']

def badge_check(id, site):
    badges = site.fetch('users/{ids}/badges', ids=id)
    badge_table = dict()
    for badge in badges['items']:
        badge_table[badge['name']] = badge['rank']
    return badge_table

def questions_answers(id, site):
    questions = site.fetch('users/{ids}/questions', ids=id)
    topAnswersTags = site.fetch('users/{ids}/top-answer-tags', ids=id)
    topTagsAnswered = dict()
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
    return len(questions['items']), datetime.datetime.fromtimestamp(mostRecentQuestion).strftime('%c'), image_name, image_name2, popularTags.keys()

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
        questionsAnswers = questions_answers([request.form['user_id']], site)
        post_frequency = posting_frequency([request.form['user_id']], site, createdUserDate, questionsAnswers[0])
        badges = badge_check([request.form['user_id']], site)
        tagAnswers = dict()
        for tag in questionsAnswers[4]:
            answerers = dict()
            tagAnswerers = tag_help([request.form['user_id']], site, tag)
            for user in tagAnswerers:
                answerers[user['user']['display_name']] = user['user']['user_id']
            tagAnswers[tag] = {k: answerers[k] for k in list(answerers)[:5]}
        timeLine = timeline([request.form['user_id']], site)
        return render_template('SearchResult.html', name = users['items'][0]['display_name'], users = users['items'][0]['display_name'], user_id= users['items'][0]['user_id'],  badges=badges, questions = questionsAnswers, question_url='static/images/{}'.format(questionsAnswers[2]), answerTags_url='static/images/{}'.format(questionsAnswers[3]), posting_url='static/images/{}'.format(post_frequency), tagAnswerers=tagAnswers, timeline='static/images/{}'.format(timeLine))
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
            questionsAnswers = questions_answers(listSameUsersID, site)
            createdUserDate = users['items'][0]['creation_date']
            post_frequency = posting_frequency(listSameUsersID, site, createdUserDate, questionsAnswers[0])
            badges = badge_check(listSameUsersID, site)
            tagAnswers = dict()
            for tag in questionsAnswers[4]:
                answerers = dict()
                tagAnswerers = tag_help(listSameUsersID, site, tag)
                for user in tagAnswerers:
                    answerers[user['user']['display_name']] = user['user']['user_id']
                tagAnswers[tag] = {k: answerers[k] for k in list(answerers)[:5]}
            timeLine = timeline(listSameUsersID, site)
            return render_template('SearchResult.html', name = processed_name, users = listSameUsers, user_id= listSameUsersID, questions = questionsAnswers,  badges=badges, question_url='static/images/{}'.format(questionsAnswers[2]), answerTags_url='static/images/{}'.format(questionsAnswers[3]), posting_url='static/images/{}'.format(post_frequency), tagAnswerers=tagAnswers, timeline='static/images/{}'.format(timeLine))

if __name__ == '__main__':
    app.run(debug=True)