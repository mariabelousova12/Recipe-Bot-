# Recipe-Bot
Configuration. .env File

You must place a .env file in the root directory with content similar to this:

TOKEN=<telegram bot api token>
DB_NAME=<name for SQLite file>

Image Storage. images.db Directory

Images related to recipes should be stored in the images.db directory. The image file name should be <recipe id>.jpg. If an image is not found for a specific recipe, the default.jpg image will be used.

Note: If there is no image for a recipe, the images.db/default.jpg image must exist; otherwise, the bot will not send recipes or menu options for selection.

Running
To run the bot, you will need to use the pipenv utility. You can install it with the following command:

pip install pipenv

Use the following commands to start the bot:
cd /path/to/telegram-recipe-bot
pipenv run python main.py
