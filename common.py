bot_name = 'FH-GoalieBot'
def get_current_threads(subreddit,limit=200):
    bot_threads = []
    threads = subreddit.hot(limit=limit)
    for thread in threads:
        if thread.author == bot_name:
            if thread not in bot_threads:
                bot_threads.append(thread)
    threads = subreddit.new(limit=limit)
    for thread in threads:
        if thread.author == bot_name:
            if thread not in bot_threads:
                bot_threads.append(thread)
    return bot_threads


def get_unanswered_comments(thread,number=1):
    unanswered_authors = []
    unanswered_comments = []
    if hasattr(thread,'comments'):
        for comment in thread.comments:
            count = 0
            if hasattr(comment, 'replies'):
                for reply in comment.replies:
                    if len(reply.body) > 20:
                            count += 1
                if count <= number and str(comment.banned_by) == 'None' and comment.author not in unanswered_authors:
                    unanswered_comments.append(comment)
                    unanswered_authors.append(comment.author)
    return unanswered_comments

def get_numbered_helped(comment_replies,author):
    number_helped = 0
    for reply in comment_replies:
        if str(reply.author) == str(author):
            number_helped += 1
    return number_helped


def get_comment_replies(thread):
    comment_replies = []
    if hasattr(thread,'comments'):
        for comment in thread.comments:
            if hasattr(comment, 'replies'):
                for reply in comment.replies:
                    if len(reply.body) > 20:
                        comment_replies.append(reply)
    return comment_replies


def get_num_stickies(subreddit):
    stickied = 0
    for thread in subreddit.hot(limit=2):
        if thread.stickied:
            stickied += 1
    print('STICKIES', stickied)
    return stickied


def remove_yesterday_stickies(subreddit, date, time_zone):
    for thread in subreddit.hot(limit=2):
        if str(thread.author) == bot_name:
            title = str(thread.title)
            if 'News and Discussions' in title and date not in title:
                thread.mod.sticky(state=False)
            if 'Fantasy Hockey Megathread' in title and (date not in title or time_zone not in title):
                thread.mod.sticky(state=False)
