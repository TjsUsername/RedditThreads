import sys
import datetime
from collections import defaultdict
from pytz import timezone
import praw
import yaml
from common import *
from post_player_discussions import *

bot_name = "FH-GoalieBot"
bot_pw = "XXXXXXXXXX"
client_id = 'XXXXXXXXX'
client_secret = 'XXXXXXXXXXXXX'

def calculate_overall_leader_index(number=10):
    user_scores_sortable = []
    over_all_help_count = defaultdict(int)
    for key, value in over_all_help_count.items():
        user_scores_sortable.append((value, key))
    user_scores_sortable.sort()
    user_scores_sortable.reverse()
    table = "\n----\n**The following users have helped the most people in all of the threads:**"
    table += "\n\nUser | # Helped in thread\n-------|:-----:"
    for user in user_scores_sortable[:number]:
        table += '\n%s|%s' % (user[1], user[0])
    return table


def calculate_leader_index(thread, overall_help_count, number=5):
    # Get the help count of all the threads for all users.
    help_count_thread = defaultdict(int)
    for comment in thread.comments:
        if hasattr(comment, 'replies') and len(comment.replies) > 0:
            for reply in comment.replies:
                try:
                    help_count_thread[reply.author.name] += 1
                except Exception as e:
                    print(e)
                    pass

    user_scores_sortable = []
    for key, value in help_count_thread.items():
        user_scores_sortable.append((value, key))

    user_scores_sortable.sort()
    user_scores_sortable.reverse()
    table = "\n----\n**The following users have helped the most people in this thread:**"
    table += "\n\nUser | # Helped in thread\n-------|:-----:"
    for user in user_scores_sortable[:number]:
        table += '\n%s|%s' % (user[1], user[0])

    return table


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


def create_unanswered_index(thread, help_count_all, length=20, text=True, show_percents=False):
    rows = []
    table = "\n\n-------------\n\n"
    if text:
        table += "**The following posts have less than two replies in this thread. Please respond directly to the OP or the Bot will not pick up your comment. Please provide quality replies, short answers will be ignored.** \n\n **Would you like your post to be at the top of the list? Remember that the table is sorted by those that have helped the most other users.** \n\n"
    table += '\n\nUser | # Helped in thread | # Helped in all threads | Direct Link'
    table += '\n----|:-----:|:-----:|----'

    unanswered_comments = get_unanswered_comments(thread)
    if len(thread.comments) > 0:
        percent_answered = int((1 - (float(len(unanswered_comments)) / len(thread.comments))) * 100)
    else:
        percent_answered = 100
    comment_replies = get_comment_replies(thread)

    for comment in unanswered_comments:
        try:
            author = comment.author.name

            # Comments in Current Thread
            author_replies = get_numbered_helped(comment_replies, author)

            # Comments in All Threads
            if help_count_all[author]:
                author_all_replies = help_count_all[author]
            else:
                author_all_replies = 0

            # Link to Users Comment
            link = comment.permalink

            # Time Stamp
            created = int(comment.created) * -1

            # Append to tuple for free sort
            rows.append((author_replies, author_all_replies, created, author, link))
        except Exception as e:
            print(e)
            pass

    rows.sort()
    rows.reverse()
    num_of_unanswered = length
    if len(rows) > 0:
        for row in rows[0:num_of_unanswered]:
            table += "\n%s | %s | %s | [Comment](%s)" % (row[3], row[0], row[1], row[4])
        if len(rows) > num_of_unanswered:
            table += '\n**and %d others.**| | ' % (len(rows) - num_of_unanswered)
        table += "\n\n^(This table will be updated every ~15 minutes.)"
        if show_percents:
            table += '\n\n**%s%% of users have been helped in this thread**' % percent_answered

        return table
    return ""


def post_index_thread(index_body):
    # POST INDEX THREAD
    index_title = 'Fantasy Hockey Megathread: [Index] - %s %s, %s' % (current_day, thread_zone, current_date)
    thread_found = False
    current_threads = get_current_threads(subreddit)
    for thread in current_threads:
        if index_title == thread.title:
            thread_found = thread
        if 'Fantasy Hockey Megathread' in thread.title and current_date not in thread.title:
            thread.mod.sticky(state=False, bottom=False)

    if thread_found:
        print('EDITING INDEX', index_title)
        thread_found.edit(index_body)
    else:
        print('SUBMITTING THREAD', index_title)
        submitted_thread = subreddit.submit(index_title, selftext=index_body)
        if submitted_thread.link_flair_text != "Index":
            submitted_thread.mod.flair(text='Index', css_class='index')
        submitted_thread.mod.sticky(state=True, bottom=False)
        submitted_thread.mod.lock()


def     calculate_index_length(index_body, news_link, overall_help_count):
    index_length = 0
    index_num = 20

    while index_length == 0 or index_length > 15000:
        threads_for_index = []
        print(index_num)
        # Edit all the threads
        threads_for_index = []
        for thread, thread_body, thread_config in found_threads:
            index = create_unanswered_index(thread, overall_help_count, length=index_num, text=False,
                                            show_percents=config['show_percents'])
            threads_for_index.append((thread, index))

        index_body = ""
        index_body += get_wiki(subreddit, 'index')
        if news_link:
            index_body += "\n#[News/Player Discussions](%s)\n\n" % news_link
        index_body += calculate_overall_leader_index()
        for thread in threads_for_index:
            index_body += "\n --- \n\n"
            index_body += "#[%s](%s)" % (thread[0].title, thread[0].permalink)
            index_body += thread[1]
        index_length = len(index_body)
        print(index_length)
        index_num -= 1
    return index_body


def get_wiki(subreddit, wiki_name):
    try:
        wiki_source = subreddit.wiki['ffbot/%s' % wiki_name].content_md
        wiki_source = wiki_source.replace('&lt;', '<').replace('&gt;', '>')
    except:
        wiki_source = "No Wiki Found"

    return wiki_source


def get_overall_help_count(found_threads):
    help_count_all = defaultdict(int)
    for thread, thread_body, thread_config in found_threads:
        for comment in thread.comments:
            if hasattr(comment, 'replies') and len(comment.replies) > 0:
                for reply in comment.replies:
                    try:
                        help_count_all[reply.author.name] += 1
                    except:
                        pass
    return help_count_all


def get_thread_zone(config, hour):
    if config['posts_per_day'] == 3:
        if hour >= 6 and hour < 11:
            thread_zone = "Morning"
        elif hour >= 11 and hour < 18:
            thread_zone = "Afternoon"
        else:
            thread_zone = "Evening"
    elif config['posts_per_day'] == 2:
        if hour >= 5 and hour < 12:
            thread_zone = "Morning"
        else:
            thread_zone = "Evening"
    else:
        thread_zone = ""

    return thread_zone

this_date = datetime.datetime.now().astimezone(timezone('US/Central'))

hour = int(this_date.strftime("%H"))

r = praw.Reddit(client_id=client_id,
                client_secret=client_secret,
                password=bot_pw,
                user_agent='FantasyBot',
                username=bot_name)

# Not creating a new thread until 6am
if hour < 6:
    this_date = this_date - datetime.timedelta(days=1)

print(this_date)

current_date = this_date.strftime("%m/%d/%Y")
current_day = this_date.strftime('%a')
current_day_full = this_date.strftime('%A').lower()
hour = int(this_date.strftime("%H"))

config = yaml.load(open("%s.yaml" % sys.argv[1]).read())
thread_zone = get_thread_zone(config, hour)
print("Posting to Sub: %s" % config['subreddit'])
subreddit = r.subreddit(config['subreddit'])
current_threads = get_current_threads(subreddit, limit=1000)
found_threads = []
remove_yesterday_stickies(subreddit, current_date, thread_zone)

# Find all Threads, submit new one if there is no thread.

thread_configs = sorted(config['threads'], key=lambda k: k['title'])

for thread_config in thread_configs:
    if 'day' in thread_config and thread_config['day'] != current_day_full:
        continue

    thread_found = False

    # Get Thread Body
    wiki = get_wiki(subreddit, thread_config['wiki'])
    if config['wdis_replace']:
        if thread_config['wiki'] == 'wdis':
            position = thread_config['title'].split(' ')[1]
            wiki = wiki.replace('<REPLACE>', position)

    thread_title = '[%s] - %s %s, %s' % (thread_config['title'], current_day, thread_zone, current_date)

    # See if thread already exists.
    for thread in current_threads:
        if thread_title == str(thread.title):
            print('ALREADY SUBMITTED, USING:', thread_title)
            if thread.num_comments < 2000:
                thread.comments.replace_more(limit=None)
            found_threads.append((thread, wiki, thread_config))
            thread_found = True
            break

    if not thread_found:
        print('SUBMITTING THREAD', thread_title)
        submitted_thread = subreddit.submit(thread_title, selftext=wiki)
        submitted_thread.mod.suggested_sort(sort='new')
        submitted_thread.mod.flair(text=thread_config['flair_text'], css_class=thread_config['flair_css'])
        if 'sticky' in thread_config and thread_config['sticky']:
            submitted_thread.mod.sticky(state=True, bottom=True)

        found_threads.append((submitted_thread, wiki, thread_config))

overall_help_count = get_overall_help_count(found_threads)

# EDIT THE POSTS
for thread, thread_body, thread_config in found_threads:
    if 'no_table' in thread_config:
        continue
    index = ""
    index = create_unanswered_index(thread, overall_help_count, length=40, show_percents=config['show_percents'])
    thread_body += calculate_leader_index(thread, overall_help_count)
    thread_body += index
    print('EDITING THREAD', thread.title)
    thread.edit(thread_body)

if config['index']:
    # GET THE PROPER LENGTH FOR THE INDEXES
    index_body = get_wiki(subreddit, 'index')
    if config['news_and_discussion']:
        news_link = post_news_and_discussions(r, subreddit, current_threads, current_day, current_date)
    else:
        news_link = False
    index_body = calculate_index_length(index_body, news_link, overall_help_count)
    post_index_thread(index_body)
