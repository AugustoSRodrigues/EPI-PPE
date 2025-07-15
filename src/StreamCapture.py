import socket
import cv2
import numpy as np
import threading
import time
import requests
import json
import os
from pathlib import Path

class RTSPStreamCapture:
    """
    Classe RTSPStreamCapture
    Esta classe é responsável por capturar frames de um stream RTSP, enviar esses frames para um servidor via socket TCP, receber respostas do servidor (como detecções de EPI), desenhar anotações nos frames conforme as respostas e, opcionalmente, enviar mensagens de teste via Telegram.
    Atributos:
        rtsp_url (str): URL do stream RTSP de onde os frames serão capturados.
        telegran (list): Lista de IDs de chat do Telegram para envio de notificações.
        host (str): Endereço do host do servidor para onde os frames serão enviados.
        port (int): Porta do servidor para envio dos frames.
        capture_interval (float): Intervalo em segundos entre capturas de frames.
        capture_thread (threading.Thread): Thread responsável pela captura e envio dos frames.
        running (bool): Indica se a captura está ativa.
    Métodos:
        start():
            Inicia a thread de captura e envio dos frames.
        stop():
            Para a thread de captura e aguarda sua finalização.
        capture_and_send():
            Realiza a captura de um frame a cada intevalo(capture_inteval) do stream RTSP  e envia o servidor, aguardando e processando a resposta.
        send_frame(frame):
            Envia um frame para o servidor via socket TCP, recebe a resposta (por exemplo, detecções de EPI) e chama o método de anotação dos frames.
        draw_boxes(frame, boxes, color=(0, 0, 255)):
            Desenha caixas delimitadoras e rótulos nos frames de acordo com as detecções recebidas, indicando violações de EPI. Salva o frame anotado em disco caso haja violação.
        send_message_test(text='test'):
            Envia uma mensagem de texto de teste para os chats do Telegram configurados, utilizando um endpoint Flask.
    Notas:
        - A classe depende de bibliotecas externas como cv2, numpy, socket, threading, time, json, requests e pathlib.
        - O método draw_boxes salva frames anotados no diretório './ocorrencias' quando há violação de EPI.
        - O envio de mensagens para o Telegram depende da configuração do atributo flask_url.
    """
    def __init__(self, rtsp_url, telegran=[], host='localhost', port=13750, capture_interval=1.0):
        self.rtsp_url = rtsp_url
        self.telegran = telegran
        self.host = host
        self.port = port
        self.capture_interval = capture_interval
        self.capture_thread = threading.Thread(target=self.capture_and_send)
        self.running = False

    def start(self):
        self.running = True
        self.capture_thread.start()

    def stop(self):
        self.running = False
        self.capture_thread.join()

    def capture_and_send(self):
        cap = cv2.VideoCapture(self.rtsp_url)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cont_frames = 0
       

        while self.running:
            ret, frame = cap.read()
            if ret:
                if cont_frames % int(fps * self.capture_interval) == 0:
                    self.send_frame(frame)
            cont_frames += 1

            
        cap.release()

    def send_frame(self, frame):
        """
        Envia um frame para o servidor via socket TCP, recebe a resposta do servidor (por exemplo, detecções de EPI)
        e chama o método de anotação dos frames.

        Args:
            frame (np.ndarray): Frame de imagem a ser enviado para o servidor.

        Retorna:
            None
        """
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))
            _, buffer = cv2.imencode('.jpg', frame)
            frame_data = buffer.tobytes()
            client_socket.sendall(len(frame_data).to_bytes(4, 'big'))
            client_socket.sendall(frame_data)
        except Exception as e:
            print(f"Erro ao enviar frame: {e}")
        try:
            response_length = int.from_bytes(client_socket.recv(4), 'big')
            response_data = b""
            while len(response_data) < response_length:
                packet = client_socket.recv(4096)
                if not packet:
                    break
                response_data += packet
            response = json.loads(response_data.decode('utf-8'))
            client_socket.close()
        except Exception as e:
            print(f"Erro ao receber resposta: {e}")
        print(response)
        self.draw_boxes(frame, response)
        
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))

            
            _, buffer = cv2.imencode('.jpg', frame)
            frame_data = buffer.tobytes()

            client_socket.sendall(len(frame_data).to_bytes(4, 'big'))

            client_socket.sendall(frame_data)
        except Exception as e:
            print(f"Erro ao enviar frame: {e}")
        try:
            response_length = int.from_bytes(client_socket.recv(4), 'big')

            response_data = b""
            while len(response_data) < response_length:
                packet = client_socket.recv(4096)
                if not packet:
                    break
                response_data += packet

            response = json.loads(response_data.decode('utf-8'))
            
            
            client_socket.close()
            
        except Exception as e:
            print(f"Erro ao receber resposta: {e}")
        print(response)
        self.draw_boxes(frame,response)
    

    def draw_boxes(self, frame, boxes, color=(0, 0, 255)):
        '''Desenha caixas delimitadoras e rótulos no frame fornecido para indicar violações detectadas de EPI (Equipamento de Proteção Individual).
        Caixas delimitadoras para pessoas detectadas são desenhadas com linhas sólidas vermelhas ou verdes, dependendo da conformidade com o EPI. Para cada item de EPI ausente, um retângulo tracejado com cantos sólidos é desenhado ao redor da região relevante, e um rótulo indicando o item ausente é adicionado. Se qualquer violação de EPI for detectada, o frame anotado é salvo no diretório './ocorrencias' com um nome de arquivo baseado em timestamp.
        Args:
            frame (np.ndarray): O frame de imagem no qual desenhar as caixas e rótulos.
            boxes (list): Uma lista de detecções, onde cada detecção contém coordenadas da caixa delimitadora e informações de status do EPI.
            color (tuple, opcional): A cor BGR para desenhar as caixas e rótulos de violação. Padrão é (0, 0, 255) (vermelho).
        Retorna:
            None'''
        
        ppe_name = {0:'Capacete', 1:'Veste', 2:'Oculos', 3:'Luvas', 4:'Calcados'}
        copy = frame.copy()
        no_ppe = False
        person = False

        def draw_dashed_with_solid_ends(img, pt1, pt2, color, thickness=2, dash_length=15, gap_length=10, solid_length=20):
            """Desenha linha tracejada com as pontas sólidas entre pt1 e pt2."""
            dist = int(np.linalg.norm(np.array(pt2) - np.array(pt1)))
            if dist == 0:
                return
            
            direction = (np.array(pt2) - np.array(pt1)) / dist
            
            start_solid_end = np.array(pt1) + direction * solid_length
            cv2.line(img, tuple(map(int, pt1)), tuple(map(int, start_solid_end)), color, thickness)
            
            end_solid_start = np.array(pt2) - direction * solid_length
            cv2.line(img, tuple(map(int, end_solid_start)), tuple(map(int, pt2)), color, thickness)
            
            current = start_solid_end
            while np.linalg.norm(current - end_solid_start) > dash_length:
                next_dash_end = current + direction * dash_length
                if np.linalg.norm(next_dash_end - start_solid_end) + solid_length > dist - solid_length:
                    break
                cv2.line(img, tuple(map(int, current)), tuple(map(int, next_dash_end)), color, thickness//2)
                current = next_dash_end + direction * gap_length
                if np.linalg.norm(current - end_solid_start) < 0:
                    break
        def draw_line(img, pt1, pt2, color, thickness=10):
            
            x1, y1 = int(pt1[0]), int(pt1[1])
            x2, y2 = int(pt2[0]), int(pt2[1])
            
            draw_dashed_with_solid_ends(img, (x1, y1), (x2, y1), color, thickness)
            draw_dashed_with_solid_ends(img, (x1, y2), (x2, y2), color, thickness)
            
            draw_dashed_with_solid_ends(img, (x1, y1), (x1, y2), color, thickness)
            draw_dashed_with_solid_ends(img, (x2, y1), (x2, y2), color, thickness)

        for det in boxes:
            xp1, yp1, xp2, yp2 = det[0]
            for i, ppe in enumerate(det[1]):
                if ppe[0] == False:
                    no_ppe = True
                    person = True
                    x1, y1, x2, y2 = ppe[2]
                    draw_line(copy, (x1, y1), (x2, y2), color=color)
                    txt =  f'Nao Usando {ppe_name[i]}'
                    copy = cv2.putText(copy, txt, (x1, y1+40), cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.5, color=color, thickness=2)
            if person:
                cv2.rectangle(copy, (xp1, yp1), (xp2, yp2), color=(0,0,255), thickness=10)
                person = False
            else:
                cv2.rectangle(copy, (xp1, yp1), (xp2, yp2), color=(0,255,0), thickness=10)
        
        if no_ppe or not no_ppe:
            ocorrencias_dir = Path('./ocorrencias')
            ocorrencias_dir.mkdir(parents=True, exist_ok=True)
            url = str(ocorrencias_dir / str(time.time()))
            print(f"Salvando frame com violação de EPI em: {url}.jpg")
            cv2.imwrite(url+'.jpg', copy)



    def send_message_test(self, text='test'):
        """
        Envia uma mensagem de texto de teste para todos os IDs de chat do Telegram configurados.

        Parâmetros:
            text (str): Texto da mensagem a ser enviada. Padrão é 'test'.

        """
        if not self.flask_url:
            print("URL do servidor Flask não configurada.")
            return
        for chat_id in self.telegran:
            payload = {
                "to": chat_id,
                "text": text
            }
            try:
                response = requests.post(f"{self.flask_url}/api/bot/telegram/send-text", json=payload)
                if response.status_code == 200:
                    print(f"Mensagem enviada para o Telegram: {text}")
                else:
                    print(f"Falha ao enviar mensagem. Resposta: {response.text}")
            except Exception as e:
                print(f"Erro ao enviar mensagem para o Flask: {e}")

