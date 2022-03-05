import requests

def telegram_bot_sendtext(bot_message):
    
    bot_token = '1712128759:AAGbxIkYrtYJRSgMUn2B7sdTpXqJiHBVAi4'
    bot_chatID = '-535260054'
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message

    response = requests.get(send_text)

    return response.json()
