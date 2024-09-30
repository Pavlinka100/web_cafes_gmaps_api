#THE TASK DESCRIPTION
#On day 66, we create an API that serves data on cafes with wifi and good coffee.
# Today, you're going to use the data from that project to build a fully-fledged website to display the information.
# Included in this assignment is an SQLite database called cafes.db that lists all the cafe data.
#Using this database and what you learnt about REST APIs and web development, create a
# website that uses this data. It should display the cafes, but it could also allow people to add new cafes, update price, delete cafes, search based on location.


#comment to the solution:
# using google maps apis to make this web page easy to work with and customer friendly as it provides huge amount of available data
#data deletion is possible with key only (for both web and API),key is hashed and hidden in system vars, the task was not about creating account management
#I am using just some  bootstrap templates to finish task given and create some look, it is full responsive
#last lines of code contains the original API code from the course, leaving it as it is, as it cannot destroy the web, but in real production it should have better input validation
#I was NOT searching for examples of existing solution instead tried something on my own to learn something,

#note to run this:
#there is/was a bug in flask-googlemaps package which prevented the map to be shown, fixed by using Flask-GoogleMaps-0.4.1.1 version
