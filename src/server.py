import socket
import time
import cv2
import numpy as np
import threading
import json

import torch
import NN
import os
from pathlib import Path


model_path = Path('model') / 'best.pt'
model = NN.PPE(str(model_path))

def handle_client(client_socket):
    """
    Processa imagens recebidas de clientes para detecção de EPI (Equipamentos de Proteção Individual).
    Esta função recebe uma conexão de socket de um cliente, lê uma imagem enviada em formato codificado,
    decodifica a imagem, processa-a utilizando um modelo de detecção de EPI e retorna o resultado ao cliente.
    O protocolo de comunicação espera que o cliente envie primeiro o tamanho da imagem em 4 bytes (big-endian),
    seguido pelos dados da imagem. O resultado do processamento é enviado de volta em formato JSON.
    Parâmetros:
        client_socket (socket.socket): Socket conectado ao cliente que enviou a imagem.
    Fluxo:
        1. Recebe o tamanho da imagem.
        2. Recebe os dados da imagem.
        3. Decodifica e processa a imagem para detecção de EPI.
        4. Envia o resultado do processamento ao cliente.
    Em caso de erro, a exceção é registrada e o socket é fechado.
    """
    try:
        
        frame_length = int.from_bytes(client_socket.recv(4), 'big')
        
        frame_data = b""
        while len(frame_data) < frame_length:
            packet = client_socket.recv(4096)
            if not packet:
                break
            frame_data += packet

        frame = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        
        status = model.run(frame)
        response = json.dumps(status).encode('utf-8')
        client_socket.send(len(response).to_bytes(4, 'big'))

        client_socket.send(response)

    except Exception as e:
        print(f"Erro ao processar o cliente: {e}")
    finally:
        client_socket.close()

    
def start_server(host='localhost', port=13750):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Servidor rodando em {host}:{port}")
   

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Conexão de {addr}")
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()
    except Exception as e:
        print(f"Erro no servidor: {e}")
    finally:
        server_socket.close()
if __name__ == "__main__":  
    print("Modelo carregado com sucesso.")
    start_server()
