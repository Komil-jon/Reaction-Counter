# Advanced automatic reaction counter in Telegram platform
##########################################################

# Description
Using flask framework, MongoDB for remote database and telegram open API to automate the process of counting and reporting the results of Telegram reactions in groups.

# Deployment
1. ## Clone/Fork this repository
2. ## MongoDB
   - Create database 'reactioneer' and collection 'users'
3. ## Environmental variables
   - ADMIN - your telegram ID
   - BOT_TOKEN - your telegram bot's ID
   - PASSWORD - MongoDB password
   - USERNAME - MongoDB username
   
# Future Plans
- *Removing the most hated message from groups to establish integrity in groups*
- *To add new titles for group members based on the reactions they get/put*
- *Training the model with large dataset to predict when which user is more likely to put reactions and the type of these reactions*
