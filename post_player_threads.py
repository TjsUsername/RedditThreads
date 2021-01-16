import praw,time,re,random,datetime
from datetime import date, timedelta
from common import *


def get_days_since_monday():
    days = 1
    the_day = date.today()
    if the_day.weekday() != 0:
        while the_day.weekday() != 0:
            print(the_day.weekday())
            days += 1
            the_day = the_day - timedelta(days=1)
    else:
        return 7
    return days


def get_threads_by_flair(subreddit, query, days, flair):
    current_time = int(time.time())
    threads = []
    posts_boy_flair = subreddit.search(query, time_filter='week', sort='new')
    for thread in posts_boy_flair:
        sub_age = (current_time - thread.created_utc) / 60 / 60 / 24
        if sub_age < days:
            threads.append((thread.title,thread.permalink))

    if len(threads) > 0:
        html = "\n\n#Recent %s\n" % flair
        for post in threads:
            html += "\n* [%s](%s)" % (post[0],post[1])
        return html
    return ""

def post_news_and_discussions(r,subreddit,current_threads,current_day,current_date):
    html = ""
    title = 'News and Discussions - %s %s' % (current_day,current_date)
    player_discussions = get_threads_by_flair(subreddit,'flair:player',2,"Player Discussions")
    quality_posts = get_threads_by_flair(subreddit,'flair:quality',get_days_since_monday(),"Quality Posts")
    mod_posts = get_threads_by_flair(subreddit,'flair:mod',get_days_since_monday(),"Mod Posts")
    news = get_threads_by_flair(subreddit,'flair:news',2,"News")

    html = ''
    html += mod_posts
    html += quality_posts
    html += news
    html += player_discussions

    current_news_and_discussion_thread = False

    for new_news_and_discussion_thread in current_threads:
        if new_news_and_discussion_thread.title == title:
            current_news_and_discussion_thread = new_news_and_discussion_thread
            break

    if not current_news_and_discussion_thread:
        print('SUBMITTING:' , title)
        new_news_and_discussion_thread = subreddit.submit(title,selftext=html)
        new_news_and_discussion_thread.mod.flair(text='Daily Thread', css_class='daily')
        new_news_and_discussion_thread.mod.lock()
        return new_news_and_discussion_thread.permalink
    else:
        print('EDITING:', current_news_and_discussion_thread.title)
        current_news_and_discussion_thread.edit(html)
        return current_news_and_discussion_thread.permalink
