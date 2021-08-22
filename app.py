from flask import Flask, request, render_template, redirect
import random
import time

# - Mongo
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client['sportsMarket']

marketDB = db.market
goldTeamsDB = db.goldTeams
goldLeaguesDB = db.goldLeagues

# - Flask
app = Flask(__name__)


# - Landing
@app.route('/')
def landing():
    return render_template('home.html', player=marketDB.find_one({}, {'_id': False}),
                           playerValue=marketDB.find_one({}, {'_id': False}),
                           goldTeams=goldTeamsDB.find_one({}, {'_id': False}),
                           myTeam=goldTeamsDB.find_one({}, {'_id': False})['teams']['Team Name']['roster'],
                           myGold=goldTeamsDB.find_one({}, {'_id': False})['teams']['Team Name']['goldChips'],
                           goldLeagues=goldLeaguesDB.find_one({}, {'_id': False}),
                           myGoldLeagues=goldTeamsDB.find_one({}, {'_id': False})['teams']['Team Name'][
                               'goldLeagues'],
                           myTeamNum=goldTeamsDB.find_one({}, {'_id': False})['teams']['Team Name']['players'])


# - Market activity
@app.route('/market')
def market():
    return render_template('market.html', player=marketDB.find_one({}, {'_id': False}),
                           playerValue=marketDB.find_one({}, {'_id': False}),
                           myGold=goldTeamsDB.find_one({}, {'_id': False})['teams']['Team Name']['goldChips'],
                           myTeamNum=goldTeamsDB.find_one({}, {'_id': False})['teams']['Team Name']['players'])


@app.route('/buy/<player>/<team>', methods=['GET'])
def buyingGold(player, team):
    # adds player to team and subtracts chips
    if goldTeamsDB.find_one({}, {'_id': False})['teams'][team]['players'] < 25:  # Checks if roster is less than 25
        if player in goldTeamsDB.find_one({}, {'_id': False})['teams'][team][
            'roster']:  # Checks if the player is already on the team
            if goldTeamsDB.find_one({}, {'_id': False})['teams'][team]['goldChips'] + \
                    marketDB.find_one({}, {'id': False})[player]['value'] >= 0:  # makes sure you have enough chips
                # adds value to the player
                result = marketDB.find_one({}, {'_id': False})
                result[player]["value"] += 2
                resultUpdate = marketDB.update_one({}, {"$set": result})

                # takes gold from team
                result2 = goldTeamsDB.find_one({}, {'_id': False})
                result2['teams'][team]['goldChips'] -= result[player]['value']
                result2['teams'][team]['roster'][player] += 1  # adds to a player already on your team
                result2['teams'][team]['players'] += 1  # adds to player count
                result2Update = goldTeamsDB.update_one({}, {"$set": result2})

        else:
            if goldTeamsDB.find_one({}, {'_id': False})['teams'][team]['goldChips'] + \
                    marketDB.find_one({}, {'id': False})[player]['value'] >= 0:  # Checks if user has enough gold
                # adds value to the player
                result = marketDB.find_one({}, {'_id': False})
                result[player]["value"] += 2
                resultUpdate = marketDB.update_one({}, {"$set": result})

                # takes gold from team
                result2 = goldTeamsDB.find_one({}, {'_id': False})
                result2['teams'][team]['goldChips'] -= result[player]['value']
                result2['teams'][team]['roster'][player] = 1  # adds player to your team
                result2['teams'][team]['players'] += 1  # adds to player count
                result2 = goldTeamsDB.update_one({}, {"$set": result2})

    return redirect("/market", code=302)


@app.route('/sell/<player>/<team>', methods=['GET'])
def sellingGold(player, team):
    if goldTeamsDB.find_one({}, {'_id': False})['teams'][team]['players'] >= 1 and player in \
            goldTeamsDB.find_one({}, {'_id': False})['teams'][team][
                'roster']:  # Checks if there is more than oneplayer on the team and if the player is on the roster
        # take value from the player
        result = marketDB.find_one({}, {'_id': False})
        result[player]["value"] -= 2
        resultUpdate = marketDB.update_one({}, {"$set": result})

        # adds to gold chips
        result2 = goldTeamsDB.find_one({}, {'_id': False})
        result2['teams'][team]['goldChips'] += result[player]['value']
        result2['teams'][team]['roster'][player] -= 1  # subtracts a player already on your team
        result2['teams'][team]['players'] -= 1  # subtracts player count

        if result2['teams'][team]['roster'][
            player] == 0:  # if player count for specfic player is 0, take them off the team
            result2['teams'][team]['roster'].pop(player)

        result2update = goldTeamsDB.update_one({}, {"$set": result2})
    return redirect("/myTeam/" + team, code=302)


# - Team
@app.route('/myTeam/<team>', methods=['GET'])
def myTeam(team):
    return render_template('roster.html', player=marketDB.find_one({}, {'_id': False}),
                           playerValue=marketDB.find_one({}, {'_id': False}),
                           goldTeams=goldTeamsDB.find_one({}, {'_id': False}),
                           myTeam=goldTeamsDB.find_one({}, {'_id': False})['teams'][team]['roster'],
                           myGold=goldTeamsDB.find_one({}, {'_id': False})['teams'][team]['goldChips'],
                           goldLeagues=goldLeaguesDB.find_one({}, {'_id': False}),
                           myGoldLeagues=goldTeamsDB.find_one({}, {'_id': False})['teams'][team][
                               'goldLeagues'],
                           myTeamNum=goldTeamsDB.find_one({}, {'_id': False})['teams'][team]['players'],
                           myTeamName=team)


# - Leagues
@app.route('/leagues', methods=['GET'])
def leagues():
    return render_template('leagues.html', goldLeagues=goldLeaguesDB.find_one({}, {'_id': False}),
                           myGoldLeagues=goldTeamsDB.find_one({}, {'_id': False})['teams']['Team Name'][
                               'goldLeagues'])


@app.route('/join/<league>/<team>', methods=['GET'])
def joinGold(league: object, team: object) -> object:
    # Adding League to user
    joinL = goldTeamsDB.find_one({}, {'_id': False})
    joinL['teams'][team]['goldLeagues'].append(league)
    joinLUpdate = goldTeamsDB.update_one({}, {"$set": joinL})

    # Adding team to league
    teamToLeague = goldLeaguesDB.find_one({}, {'_id': False})
    teamToLeague[league][team] = joinL['teams'][team]['goldChips']
    teamToLeagueUpdate = goldLeaguesDB.update_one({}, {"$set": teamToLeague})

    return redirect("/gold/league/" + league, code=302)


@app.route('/gold/leagues/<tourney>', methods=['GET'])
def viewGold(tourney):
    return render_template('aLeague.html', competitors=goldLeaguesDB.find_one({})[tourney],
                           chips=goldLeaguesDB.find_one({})[tourney], current=goldTeamsDB.find_one({})['teams'])


# - Simulate market and league activity
@app.route('/simulate', methods=['GET'])
def simulate():
    # Teams added to simulation
    teams = ['simulate1', 'simulate2', 'simulate3', 'simulate4', 'simulate5']

    # Teams getting added to simulation league
    joinGold('Simulate', 'simulate1')
    joinGold('Simulate', 'simulate2')
    joinGold('Simulate', 'simulate3')
    joinGold('Simulate', 'simulate4')
    joinGold('Simulate', 'simulate5')

    # Market activity for simulated users
    i = 0
    while i < 100:
        randomPlayer = random.choice(list(marketDB.find_one({}, {'_id': False}).keys()))
        buyOrSell = [buyingGold(randomPlayer, random.choice(teams)), sellingGold(randomPlayer, random.choice(teams))]

        random.choice(buyOrSell)
        i += 1
        time.sleep(.5)

    return redirect("/market", code=302)


# - Restart Database
@app.route('/restart', methods=['GET'])
def restart():
    market = marketDB.find_one({}, {'_id': False})
    teams = goldTeamsDB.find_one({}, {'_id': False})
    league = goldLeaguesDB.find_one({}, {'_id': False})

    market = {'Lebron James': {'value': 30, 'coins': 1000, 'cards': 1000, 'volume': 0},'Steph Curry': {'value': 30, 'coins': 1000, 'cards': 1000, 'volume': 0},'Blake Griffin': {'value': 30, 'coins': 1000, 'cards': 1000, 'volume': 0},'Kevin Durant': {'value': 30, 'coins': 1000, 'cards': 1000, 'volume': 0},'James Harden': {'value': 30, 'coins': 1000, 'cards': 1000, 'volume': 0},'Cade Cunningham': {'value': 30, 'coins': 1000, 'cards': 1000, 'volume': 0},'Russell Westbrook': {'value': 30, 'coins': 1000, 'cards': 1000, 'volume': 0},'Luka Doncic': {'value': 30, 'coins': 1000, 'cards': 1000, 'volume': 0},'Giannis Antetokounmpo': {'value': 30, 'coins': 1000, 'cards': 1000, 'volume': 0},'Damian Lillard': {'value': 30, 'coins': 1000, 'cards': 1000, 'volume': 0},'Derrick Rose': {'value': 30, 'coins': 1000, 'cards': 1000, 'volume': 0}}

    teams = {'teams': {'Team Name': {'roster': {}, 'goldChips': 3000, 'goldLeagues': [], 'players': 0},"simulate1": {"roster": {}, "goldChips": 3000, "goldLeagues": [], "players": 0},"simulate2": {"roster": {}, "goldChips": 3000, "goldLeagues": [], "players": 0},"simulate3": {"roster": {}, "goldChips": 3000, "goldLeagues": [], "players": 0}, "simulate4": {"roster": {}, "goldChips": 3000, "goldLeagues": [], "players": 0},"simulate5": {"roster": {}, "goldChips": 3000, "goldLeagues": [], "players": 0}}}
    league = {'Gold_League': {}, 'Aim_High': {}, '3_Point_Tourney': {}, 'Simulate': {}}

    marketDB.update_one({}, {"$set": market})
    goldTeamsDB.update_one({}, {"$set": teams})
    goldLeaguesDB.update_one({}, {"$set": league})

    return redirect("/", code=302)


if __name__ == '__main__':
    app.run(debug=True)
