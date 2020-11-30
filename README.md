NFL Running Back Performance and Social Media Presence

Program Description: Creating a database of NFL Running Back game performance metrics and social media activity metrics using the SportsDataIO API and Twitter API.

The program pulls data from the SportsDataIO API and Twitter API and creates an output table containing the following fields: ID, PlayerName, FantasyPoints, Week, Team, Opponent, RushingYards, RushingTouchdowns, Receptions, ReceivingYards, ReceivingTouchdowns, FumblesLost, Date, GameKey, lastTweetID, TweetsSinceLastGame


Challenges:
  The process is dependent on a manually compiled crosswalk table containing the Player Name, SportsDataIO ID, and Twitter username for each player in the sample. The process is   limited to players that have had this manual exercise completed. Being manual in nature, this table does not dynamically account for trades/player transactions.
  Both the Twitter and SportsDataIO APIs have limitations. Twitter’s API introduces rate limitation constraints while the free tier SportsDataIO API introduces scrambled data.     Accessing the SportsDataIOn paid API will resolve this scrambling issue.
  The TweetsSinceLastGame aggregation metric for week 1 is a count of all tweets since the prior season’s Super Bowl. Additionally, this metric does not account for variable       week lengths (games held on Mondays, Thursdays, Sundays, and bye weeks)
  The process does not normalize for timezones.
  The process is dependent on a specific subdirectory architecture:
    /NFL Schedule Game Data
    /playerData
    /tweets

Note: The date of the Super Bowl that concluded the 2019-2020 season was used as the date of the previous game for Week 1’s calculation of Twitter activity since last game.

This project is available on github at: https://github.com/dtw19428/NFLTwitterBack.git
A summary of the required scripts is provided below:


NFLTwitterBack.ipynb
Running this procedure will call and execute the contents of each of the following procedures. This is the only procedure that must be executed. The rest support the creation of this process.
Download tweets and player performance data for NFL running backs
The result of the program is a data frame of a player’s twitter and performance stats for each week
credentials.txt stores the Twitter and SportsDataIO API keys and secrets in the following order:
  sportsdata_api_key
  twitter consumer_key
  twitter consumer_secret
  twitter access_token
  twitter access_token_secret
Dependencies
Required directory locations:
    /NFL Schedule Game Data
    /playerData
    /tweets
Required Packages:
  CSV
  Logging
  OS
  Requests
  JSON
  Datetime
  Tweepy
  Time
  Pandas

Get_NFL_Schedule_SportsdataAPI.ipynb
This program is used to access NFL schedule fixtures of a given year
NFL schedule data provided by SportsDataIO is downloaded and converted to csv format
Dependencies
Authorized SportsDataIO API key for NFL API
  https://sportsdata.io/nfl-api
Required packages:
  Requests
  Pprint
  JSON
  CSV
  Pandas

GetTweets.ipynb
This program is used to download the tweet metadata for a list of players
CSV files containing metadata are generated for each player as a result of this program
That document has been packaged with this code
Dependencies
  Authorized Twitter API key
  Input csv 'PlayerInfo.csv' which contains the players’ twitter handles
Required Packages:
  Tweepy

PlayerData.ipynb
Program to pull running back performance data (per game) from SportsDataIO
Includes fantasy football points, rushing yards, rushing touchdowns, receptions, receiving yards, receiving touchdowns, and fumbles lost
Note: the current program is based on the free API access, which scrambles the data. Accurate data must be paid for.
Dependencies
  “Running Backs Mapping Table - Sheet1.csv” file containing list of running backs to pull performance data for
Required Packages:
  Requests
  CSV
  JSON

processData.ipynb
Uses getPlayerTwitterGameStats() function from NFLTwitterBack.py to pull week by week Twitter activity and NFL game performance stats for a given player

getCombinedData.ipynb
This program generates data sets containing performance and twitter activity split out by each individual player 


