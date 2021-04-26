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


console = Console()
db = TinyDB("following.json")

auth = tweepy.OAuthHandler(os.environ["CONSUMER_KEY"], os.environ["CONSUMER_SECRET"])
auth.set_access_token(os.environ["ACCESS_TOKEN"], os.environ["ACCESS_TOKEN_SECRET"])

api = tweepy.API(auth)

user = api.get_user("aaronbassett")

following = api.friends_ids(user.id)

db.insert({"fetched_on": arrow.now().timestamp(), "following_ids": following})

now = arrow.now()
six_months_ago = now.shift(months=-6)
two_years_ago = now.shift(years=-2)
old_accounts = []
really_old_accounts = []
current_accounts = []
no_tweet_accounts = []

for follower in track(following):
    timeline = api.user_timeline(user_id=follower, count=1)
    if timeline:
        recent_tweet = timeline[0]
        status_created_on = arrow.get(recent_tweet.created_at)

        if status_created_on < two_years_ago:
            status = Markdown(
                f"[{recent_tweet.user.screen_name}](https://twitter.com/{recent_tweet.user.screen_name}) - {status_created_on.humanize()}"
            )
            really_old_accounts.append(status)

            api.destroy_friendship(user_id=recent_tweet.user.id)

        elif status_created_on < six_months_ago:
            status = Markdown(
                f"[{recent_tweet.user.screen_name}](https://twitter.com/{recent_tweet.user.screen_name}) - {status_created_on.humanize()}"
            )
            old_accounts.append(status)
        else:
            status = Markdown(
                f"[{recent_tweet.user.screen_name}](https://twitter.com/{recent_tweet.user.screen_name}) - {status_created_on.humanize()}"
            )
            current_accounts.append(status)
    else:
        no_tweet_user = api.get_user(user_id=follower)
        status = Markdown(
            f"[{no_tweet_user.screen_name}](https://twitter.com/{no_tweet_user.screen_name}) - {arrow.get(no_tweet_user.created_at).humanize()}"
        )
        no_tweet_accounts.append(status)

    time.sleep(1)


console.print(Markdown(f"# Current Accounts - {len(current_accounts)}"))

for current_account in current_accounts:
    console.print(current_account)

console.print(Markdown(f"# Old Accounts - {len(old_accounts)}"))

for old_account in old_accounts:
    console.print(old_account)

console.print(Markdown(f"# Really Old Accounts - {len(really_old_accounts)}"))

for really_old_account in really_old_accounts:
    console.print(really_old_account)

console.print(Markdown(f"# No Tweet Accounts - {len(no_tweet_accounts)}"))

for no_tweet_account in no_tweet_accounts:
    console.print(no_tweet_account)
