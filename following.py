import tweepy
import os
import arrow
from rich import print
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import track
import time
import random
from tinydb import TinyDB, Query
import click


console = Console()
db = TinyDB("following.json")
last_tweeted_on_db = TinyDB("lasttweeted.json")

auth = tweepy.OAuthHandler(os.environ["CONSUMER_KEY"], os.environ["CONSUMER_SECRET"])
auth.set_access_token(os.environ["ACCESS_TOKEN"], os.environ["ACCESS_TOKEN_SECRET"])

api = tweepy.API(auth)

user = api.get_user(os.environ["TWITTER_USER"])

following = api.friends_ids(user.id)

db.insert({"fetched_on": arrow.now().timestamp(), "following_ids": following})

now = arrow.now()
six_months_ago = now.shift(months=-6)
two_years_ago = now.shift(years=-2)
old_accounts = []
really_old_accounts = []
really_old_account_ids = []
current_accounts = []
no_tweet_accounts = []

Tweet = Query()


def current_cached_user(user_id):
    cached_user = last_tweeted_on_db.search(Tweet.user_id == user_id)

    if cached_user:
        cached_last_tweet_time = arrow.get(cached_user[0]["last_tweeted_on"])

        if cached_last_tweet_time > six_months_ago:
            current_accounts.append(follower)
            return True

    return False


def cache_user_tweeted_on(user_id, last_tweeted_on):
    cached_user = last_tweeted_on_db.search(Tweet.user_id == user_id)

    if cached_user:
        last_tweeted_on_db.update(
            {"last_tweeted_on": last_tweeted_on}, Tweet.user_id == user_id
        )
    else:
        last_tweeted_on_db.insert(
            {"user_id": follower, "last_tweeted_on": last_tweeted_on}
        )


for follower in track(following):
    if not current_cached_user(follower):
        timeline = api.user_timeline(user_id=follower, count=1)
        if timeline:
            recent_tweet = timeline[0]
            status_created_on = arrow.get(recent_tweet.created_at)
            cache_user_tweeted_on(follower, status_created_on.timestamp())

            if status_created_on < two_years_ago:
                status = Markdown(
                    f"[{recent_tweet.user.screen_name}](https://twitter.com/{recent_tweet.user.screen_name}) - {status_created_on.humanize()}"
                )
                really_old_accounts.append(status)
                really_old_account_ids.append(recent_tweet.user.id)

            elif status_created_on < six_months_ago:
                status = Markdown(
                    f"[{recent_tweet.user.screen_name}](https://twitter.com/{recent_tweet.user.screen_name}) - {status_created_on.humanize()}"
                )
                old_accounts.append(status)
            else:
                current_accounts.append(recent_tweet.user.id)
        else:
            no_tweet_user = api.get_user(user_id=follower)
            status = Markdown(
                f"[{no_tweet_user.screen_name}](https://twitter.com/{no_tweet_user.screen_name}) - {arrow.get(no_tweet_user.created_at).humanize()}"
            )
            no_tweet_accounts.append(status)

        time.sleep(1)


console.print(Markdown(f"# Current Accounts - {len(current_accounts)}"))

console.print(Markdown(f"# Old Accounts - {len(old_accounts)}"))

for old_account in old_accounts:
    console.print(old_account)

console.print(Markdown(f"# Really Old Accounts - {len(really_old_accounts)}"))

for really_old_account in really_old_accounts:
    console.print(really_old_account)

console.print(Markdown(f"# No Tweet Accounts - {len(no_tweet_accounts)}"))

for no_tweet_account in no_tweet_accounts:
    console.print(no_tweet_account)

if click.confirm(
    f"Do you want to unfollow {len(really_old_accounts)} really old accounts?"
):
    for really_old_account_id in track(really_old_account_ids):
        api.destroy_friendship(user_id=really_old_account_id)
