import requests

class BaseAIProvider:
    def generar_respuesta(self, prompt):
        raise NotImplementedError

class KoboldProvider(BaseAIProvider):
    def __init__(self, url="http://localhost:5001/api/v1/generate"):
        self.url = url

    def generar_respuesta(self, prompt):
        payload = {
            "prompt": prompt,
            "max_length": 150,
            "temperature": 0.7,
            "stop": ["Usuario:", "\n\n"]
        }
        response = requests.post(self.url, json=payload)
        data = response.json()
        return data["results"][0]["text"].strip()

def obtener_proveedor_ia():
    return KoboldProvider()