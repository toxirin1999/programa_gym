import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# Carga las variables de entorno (nuestra API key) desde el archivo .env
load_dotenv()


def preguntar_a_joi_simple(pregunta):
    """
    Función básica para enviar una pregunta a la IA y obtener una respuesta.
    """
    # 1. Inicializamos el modelo de lenguaje que vamos a usar.
    # gpt-4o es el más nuevo y recomendado. "temperature" controla la creatividad (0 = muy predecible).
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # 2. Creamos el mensaje. Usamos un SystemMessage para darle su personalidad
    # y un HumanMessage para la pregunta del usuario.
    mensajes = [
        SystemMessage(
            content="Eres Joi, una asistente de fitness IA experta, amigable y motivadora. Tu personalidad es perspicaz y alentadora."),
        HumanMessage(content=pregunta)
    ]

    # 3. Hacemos la llamada al modelo
    print("Enviando pregunta a Joi...")
    respuesta = llm.invoke(mensajes)

    # 4. Devolvemos el contenido de la respuesta
    return respuesta.content


# --- Probemos nuestra función ---
if __name__ == "__main__":
    pregunta_usuario = "¿Cuál es el ejercicio más importante para ganar fuerza en las piernas?"
    respuesta_joi = preguntar_a_joi_simple(pregunta_usuario)

    print("\n--- Respuesta de Joi ---")
    print(respuesta_joi)
