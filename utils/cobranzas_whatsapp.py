import requests

def enviar_mensaje_api(chat_id, content):
    url = "https://whatsapp-api-fondo.onrender.com/client/sendMessage/FONDO-UGAVI"
    payload = {
        "chatId": f"{chat_id}@c.us",
        "contentType": "string",
        "content": content
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("Mensaje enviado correctamente.")
            return True
        else:
            print(f"Error al enviar el mensaje: {response.status_code} - {response.text}")
            return Exception(f"Error al enviar el mensaje: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error al conectar con la API: {e}")
        return Exception(f"Error al conectar con la API: {e}")
