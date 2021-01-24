import requests
import datetime
from pytz import timezone
from tabulate import tabulate

def get_todays_games(todays_date):
    try:
        today = todays_date.strftime("%Y-%m-%d")
        response = requests.get(f'https://statsapi.web.nhl.com/api/v1/schedule?startDate={today}&endDate={today}')
        response.raise_for_status()
        games_json = response.json()['dates'][0]['games']
        table_header = ['Home', '', 'Away', '', 'Start (EST)']
        table_rows = parse_games_data(games_json)
        if not table_rows:
            return None
        markdown = tabulate(table_rows, table_header, tablefmt="github")
        return markdown
    except Exception as err:
        print(f'Error occurred: {err}')
        return None


def parse_games_data(games_json):
    rows = []
    ordered_games = sorted(games_json, key=lambda game: get_game_datetime(game).timestamp())
    for game in ordered_games:
        game_time = get_game_time(game)
        teams = game['teams']
        home = teams['home']
        away = teams['away']
        table_row = [
            away['team']['name'],
            get_team_record(away),
            home['team']['name'],
            get_team_record(home),
            game_time
        ]
        rows.append(table_row)
    return rows


def get_team_record(team):
    wins = team['leagueRecord']['wins']
    losses = team['leagueRecord']['losses']
    ot = team['leagueRecord']['ot']
    return f"{wins}-{losses}-{ot}"


def get_game_datetime(game):
    utc = datetime.datetime.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%S%z')
    local = utc.astimezone(timezone('US/Eastern'))
    return local


def get_game_time(game):
    if game['status']['detailedState'] == 'Postponed':
        return 'Postponed'

    game_time = get_game_datetime(game).strftime("%I:%M %p")
    return game_time

