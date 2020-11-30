#!//usr/bin/env python
"""
Description: 
    Download tweets and player performance data for NFL players. Requires the following file structure: 
    /NFL Schedule Game Data
    /playerData
    /tweets

credentials.txt stores the Twitter and SportsData.io API keys and secrects in the following order:
sportsdata_api_key
twitter consumer_key
twitter consumer_sectret
twitter access_token
twitter access_token_secret

Alternatively the setAPIs function can be used to set credentials

Required Python library: 
    tweepy

Output: Pandas dataframe of a player's twitter and perforance stats for each week
"""

## Used tweet_downloader.py document setup as a basis for NFLTwitterBack.py
import csv, logging, os, requests, json, datetime, tweepy, csv, time
import pandas as pd
from datetime import datetime

sportsdata_api_key = ""
twitter_consumer_key = ""
twitter_consumer_sectret = ""
twitter_access_token = ""
twitter_access_token_secret = ""


def init():
    logging.warning("initializing... ")
    global sportsdata_api_key, twitter_consumer_key, twitter_consumer_sectret,twitter_access_token,twitter_access_token_secret
    parser = argparse.ArgumentParser(description = "A downloader for NFL player data (tweet stats and performance)")
    parser.add_argument('--credentials', type=str, required = True, help = '''\
        Credential file which consists of four lines in the following order:
        sportsdata_api_key
        twitter consumer_key
        twitter consumer_sectret
        twitter access_token
        twitter access_token_secret
        ''')
    credentials = []
    with open(arguments.credentials) as fr:
        for l in fr:
            credentials.append(l.strip())
    sportsdata_api_key = str(credentials[0])
    twitter_consumer_key = str(credentials[1])
    twitter_consumer_sectret = str(credentials[2])
    twitter_access_token = str(credentials[3])
    twitter_access_token_secret = str(credentials[4])
    
def setAPIs(sd_api, tck, tcs, tat, tats):
    global sportsdata_api_key, twitter_consumer_key, twitter_consumer_sectret,twitter_access_token,twitter_access_token_secret
    sportsdata_api_key= sd_api
    twitter_consumer_key = tck
    twitter_consumer_sectret = tcs
    twitter_access_token = tat
    twitter_access_token_secret = tats
    
def getPlayerTwitterGameStats(playerSportsIOID, playerTwitterHandle, year, week="All"):
    tweets, performanceStats = openPlayerData(playerSportsIOID,playerTwitterHandle)
    NFLschedule = openGameData(year)
    stats = getAllWeeksTweetStats(year,tweets,appendSportsData(performanceStats, NFLschedule))
    if week == "All":
        return stats
    else:
        return stats.loc[stats["Week"] == int(week)]

def appendSportsData(performanceData,SeasonData):
    #for each week in the performance Data, add the game info
    #grab team from performance data, filter if team is in home or away, player can play for multiple teams
    column_names = ['ID', 'PlayerName', 'FantasyPoints', 'Week', 'Team', 'Opponent', 'RushingYards', 'RushingTouchdowns', 'Receptions', 'ReceivingYards', 'ReceivingTouchdowns', 'FumblesLost' ]
    playerTeamCombination = pd.DataFrame(columns = column_names)
    performanceData = performanceData.dropna(subset=['PlayerName'])
    for index, row in performanceData.iterrows():
        if index == 0:
            pass
        week_data = SeasonData.loc[SeasonData['Week'] == row['Week']]   
        gameDate = week_data.loc[(week_data['AwayTeam'] == row['Team']) ^ (week_data['HomeTeam'] == row['Team'])]["Date"].values[0]
        gameKey = week_data.loc[(week_data['AwayTeam'] == row['Team']) ^ (week_data['HomeTeam'] == row['Team'])]["GameKey"].values[0]
        data = {"ID": row["ID"], "PlayerName": row["PlayerName"], "FantasyPoints":row["FantasyPoints"], "Week":row["Week"], "Team":row["Team"], "Date":gameDate, "GameKey":gameKey, "Opponent":row["Opponent"],
                "RushingYards":row["RushingYards"], "RushingTouchdowns":row["RushingTouchdowns"], "Receptions":row["Receptions"], "ReceivingYards":row["ReceivingYards"], "ReceivingTouchdowns":row["ReceivingTouchdowns"], "FumblesLost":row["FumblesLost"]}
       
        playerTeamCombination = playerTeamCombination.append(data,ignore_index=True)
    return playerTeamCombination

def getTweets(playerID):
    tweets = []
    player_Data = []
    
    auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_sectret)
    auth.set_access_token(twitter_access_token, twitter_access_token_secret)
    logging.warning("Accessing Twitter with: " +twitter_consumer_key +" "+ twitter_consumer_sectret +" " + twitter_access_token + " " + twitter_access_token_secret)
    api = tweepy.API(auth)
    
    for status in tweepy.Cursor(api.user_timeline, screen_name=playerID).items():
        player_Data.append(status)
    for tweet in player_Data:
        tweetjson = json.dumps(tweet._json)
        parsedtweetjson = json.loads(tweetjson)
        tweets.append([parsedtweetjson['id'],parsedtweetjson['user']['followers_count'],parsedtweetjson['favorite_count'],parsedtweetjson['retweet_count'],parsedtweetjson['created_at']])
    return tweets

def getPlayersTweets(playerID,playerhandle):
        playertweets= []
        playerhandle = playerhandle
        try:
            playertweets = getTweets(playerhandle)
        except tweepy.TweepError:
            logging.warning("API Limit exceeded: taking a nap while processing " + str(playerhandle))
            time.sleep(900)
            playertweets = getTweets(playerhandle)
        fileName = str("tweets/"+ playerID + "_tweets"+".csv")
        with open(fileName, 'w', newline='', encoding='utf-8') as file:
            write = csv.writer(file)
            write.writerows(playertweets)

def getAllWeeksTweetStats(year, tweetsdf,playerPerformancebyWeek):
    column_names = ["ID", "PlayerName", "FantasyPoints", "Week", "Team", "Date", "GameKey", "lastTweetID","TweetsSinceLastGame"]
    playerWeeklyStatswithTweets = pd.DataFrame(columns = column_names)
    for index,row in playerPerformancebyWeek.iterrows():
        lastTweetID, tweetCount = getTweetStats(getRelevantTweets(year,row["Week"],tweetsdf,playerPerformancebyWeek))
        data = {"ID": row["ID"], "PlayerName": row["PlayerName"], "FantasyPoints":row["FantasyPoints"], "Week":row["Week"], "Team":row["Team"], "Date":row["Date"], "GameKey":row["GameKey"], "lastTweetID": lastTweetID,"TweetsSinceLastGame":tweetCount}
        playerWeeklyStatswithTweets = playerWeeklyStatswithTweets.append(data,ignore_index=True)     
    return playerWeeklyStatswithTweets

def getRelevantTweets(year, week,tweetsdf,playerPerformancebyWeek):
    tweetsBetweenGames = []
    if int(week) == 1:
        lastGameDateStr = str(int(year)-1)+"-02-03T18:30:00"
    else:
        try:
            lastGameDateStr = playerPerformancebyWeek.loc[playerPerformancebyWeek["Week"] == int(week)-1, "Date"].values[0]
        except IndexError:
            logging.warning("Player Did Not Play Week "+ str(week))
            return tweetsBetweenGames
    GameStartStr = playerPerformancebyWeek.loc[playerPerformancebyWeek["Week"] == int(week), "Date"].values[0]
    for index,row in tweetsdf.iterrows():
        dateTimeOfTweet = parseTwitterDate(row["created_at"])
        gameTime = parseSportsIODate(GameStartStr)
        if((dateTimeOfTweet <= gameTime) and (dateTimeOfTweet>= parseSportsIODate(lastGameDateStr))):
            timeTillGame = gameTime - dateTimeOfTweet
            tweetsBetweenGames.append([row["ID"],row["followers_count"],row["favorite_count"],row["retweet_count"],dateTimeOfTweet,timeTillGame])
    return tweetsBetweenGames

def getTweetStats(tweetlist):
    if len(tweetlist)<1:
        return 0,0
    else:
        sortedTweets = sorted(tweetlist, key = lambda x: x[4])
        firstTweetsinceLastGame = sortedTweets[0]
        lastTweetID = sortedTweets[-1][0]
        tweetCount = len(tweetlist)
        return lastTweetID, tweetCount

def parseSportsIODate(datestr):
    datestr = datestr.replace("T", " ")
    datestr = datestr.replace("-", "/")
    date = datetime.strptime(datestr, '%Y/%m/%d %H:%M:%S')
    return date

def parseTwitterDate(dateOfTweet):
    date = datetime.strptime(dateOfTweet,'%a %b %d %H:%M:%S +0000 %Y')
    return date

def openPlayerData(playerSDioID,playerTwitterHandle):
    #open the twitter file, if it exists (#later: if it doesn't then go fetch it)
    tweets = "tweets/"+ str(playerSDioID) +"_tweets.csv"
    performance = "playerData/"+ str(playerSDioID) +"_Performance.csv"
    if os.path.exists(tweets):
        tweets_df = pd.read_csv(tweets, sep = ",", names=["ID", "followers_count", "favorite_count", "retweet_count", "created_at"])
    else:
        logging.warning("no tweets exist for " + str(playerSDioID))
        getPlayersTweets(playerSDioID,playerTwitterHandle)
        tweets_df = pd.read_csv(tweets, sep = ",", names=["ID", "followers_count", "favorite_count", "retweet_count", "created_at"])
    if os.path.exists(performance):
        performance_df = pd.read_csv(performance, sep = ",", header = 0)
    else: 
        logging.warning("no performance data exists for " + str(playerSDioID))
        load_all_weeks_performance(playerSDioID)
        performance_df = pd.read_csv(performance, sep = ",", header = 0)
        #get the performance data
    return tweets_df, performance_df

def get_player_performance_data(player_ID, week, player_data):
    url = 'https://api.sportsdata.io/v3/nfl/stats/json/PlayerGameStatsByPlayerID/2020/' + str(week) + "/" + str(player_ID) + "?key=" + sportsdata_api_key
    response = requests.get(url)
    if response.status_code == 200 and validateJSON(response):
      api_response = response.json()
      player_struct = {'ID' : '', 'PlayerName': '', 'FantasyPoints': '', 'Week': '', 'Team': '', 'Opponent': '', 'RushingYards': '', 'RushingTouchdowns': '', 'Receptions': '', 'ReceivingYards': '', 'ReceivingTouchdowns': '', 'FumblesLost': '' }
      player_struct['ID'] = api_response['PlayerID']
      player_struct['PlayerName'] = api_response['Name']
      player_struct['Team'] = api_response['Team']
      player_struct['FantasyPoints'] = api_response['FantasyPointsYahoo']
      player_struct['Week'] = api_response['Week']
      player_struct['Opponent'] = api_response['Opponent']
      player_struct['RushingYards'] = api_response['RushingYards']
      player_struct['RushingTouchdowns'] = api_response['RushingTouchdowns']
      player_struct['Receptions'] = api_response['Receptions']
      player_struct['ReceivingYards'] = api_response['ReceivingYards']
      player_struct['ReceivingTouchdowns'] = api_response['ReceivingTouchdowns']
      player_struct['FumblesLost'] = api_response['FumblesLost']
    else: 
      player_struct = {'ID' : '', 'PlayerName': '', 'FantasyPoints': '', 'Week': '', 'Team': '', 'Opponent': '', 'RushingYards': '', 'RushingTouchdowns': '', 'Receptions': '', 'ReceivingYards': '', 'ReceivingTouchdowns': '', 'FumblesLost': '' }
      player_struct['ID'] = player_ID
      player_struct['PlayerName'] = ''
      player_struct['Team'] = 'BAL'
      player_struct['FantasyPoints'] = 0
      player_struct['Week'] = week
      player_struct['Opponent'] = ''
      player_struct['RushingYards'] = 0
      player_struct['RushingTouchdowns'] = 0
      player_struct['Receptions'] = 0
      player_struct['ReceivingYards'] = 0
      player_struct['ReceivingTouchdowns'] =0
      player_struct['FumblesLost'] = 0
    return player_data

def load_all_weeks_performance(player_ID):
    csv_columns = ['ID', 'PlayerName', 'FantasyPoints', 'Week', 'Team', 'Opponent', 'RushingYards', 'RushingTouchdowns', 'Receptions', 'ReceivingYards', 'ReceivingTouchdowns', 'FumblesLost'  ]
    player_data = []
    for the_week in range(10):
        player_data = get_player_performance_data(player_ID, the_week+1, player_data)
    write_out_name = "playerData/"+str(player_ID) + "_Performance.csv"
    with open(write_out_name, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for data in player_data:
            writer.writerow(data)
            
def validateJSON(jsonData):
    try:
        jsonData.json()
    except:
        return False
    return True

def openGameData(year):
    #create a data frame of game data (maybe )
    gameData = "NFL Schedule Game Data/" +str(year)+".csv"
    if os.path.exists(gameData): 
        gameDataDF= pd.read_csv(gameData, sep = ",", header = 0)
    else: 
        logging.warning("no NFL schedule data exists for " + str(year)+ " now getting data.")
        getNFLSchedule(year)
        gameDataDF = pd.read_csv(gameData, sep = ",", header = 0)
    return gameDataDF

def getNFLSchedule(year):
    year_id = str(year)
    api_url = "https://api.sportsdata.io/v3/nfl/scores/json/Schedules/" + year_id+ "?key=" + sportsdata_api_key
    response = requests.get(api_url)
    data     = response.json()
    filename = "NFL Schedule Game Data/" + str(year) + ".csv"
    schedule = open(filename, 'w') 
    csv_writer = csv.writer(schedule) 
    count = 0
    for game in data: 
        if count == 0: 
            header = game.keys() 
            csv_writer.writerow(header) 
            count += 1
        csv_writer.writerow(game.values())
    schedule.close()
    return(schedule)

def main():
    init()

if __name__ == "__main__":
    main()