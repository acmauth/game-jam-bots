# ThessGameJam Bot

## Description
A bot created for the Discord Server of the ThessGameJam, a game jam by ACM AUTh. The bot will have simple functions, extended in contrast with the previous bot, since it is to be used only for the specific event. It can be hosted in ACM AUTh's server for the duration of the competition.

## Functions
In this version, the bot will make use of itch.io API for registered game jams. We will try to implement a consistent voting system, supporting different types of votes (judges, community) using weights in scores, and of course parsing all final data to a csv file for 

### Database
Saves and manages information based on two tables: 
	* Teams, which store teams and its members
	* Requests, which stores pending requests for joining a team.

### Commands
* /join {team}
	* If team does not exist, create it and set the user as the team's owner. From the team's creation a private Channel with the team's name is created and a role (with the same name).
	* If the team does exist, the user will have to wait till the owner (or a member maybe?) accepts the request. 
		* Maybe when the pending request is created, the bot sends a message to the team's channel
	* If the team already has 4 members (including the owner) it prints something like "This team is full"

* /requests
	* Prints the usernames of users that sent a request to join the user's team
	* If they are not in a team it prints something like "You are not part of a team"
	* If there are no pending requests it prints something like "There are no requests"

* /accept {username}
	* If the username has sent a request for the current user's team, it allows them to join the team 
	* If the username hasnt sent a request it prints something like "No request found"

* /dismiss {username}
	* If the username has sent a request for the current user's team, it deletes the request
	* If the username hasnt sent a request it prints something like "No request found"

* /kick {username}
	* If username is part of the team AND IS NOT THE OWNER it kicks them out of the team
	* If username is not part of the team it prints "Not a member" 
	* Cant kick yourself

* /leave
	* If user is a member of a team, it removes them from the team
	* If user is an owner of a team, it gives the ownership of the team to the second member 
		* If a second member does not exist, it deletes the team (Channel, Role, entry in the database) 
	* If user is not in a team it prints "Not in a team" 

* /members {team}
	* If blank it prints the username's of the user's team
	* If a team name is given it prints the username's of that team
	* If blank and user isn't part of a team it prints "You are not in a team"
	* If a team name is given but it doesn't exist it prints "Team does not exist"

* /teams 
	* Print teams

* /submissions
	* Displays the current valid game submissions made by teams in itch.io. It returns information regarding the game's URL, ID and Title.

* /rate {game title} {rating}
	* Rate a game you have played! The game title must be from a valid submission (there are pre-chosen options) and the rating must be a floating point number between 0 and 10. Note that one cannot rate their own game.
