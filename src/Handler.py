import socket
import cv2
import numpy as np
import threading
import time
from StreamCapture import RTSPStreamCapture
from pathlib import Path

def mock_cliente():
    # Lista de links RTSP
    rtsp_links = [
        # str(Path('./videos_test/8488067-uhd_3840_2160_30fps (1).mp4').resolve()),
        str(Path('./videos_test/6000217_People_Person_3840x2160.mp4').resolve()),
        # str(Path('./videos_test/5123924_Person_People_3840x2160.mp4').resolve()),
        # str(Path('./videos_test/8488053-uhd_2160_3840_30fps.mp4').resolve())
    ]

    # Inicializa e inicia as capturas de cada link
    captures = [RTSPStreamCapture(url) for url in rtsp_links]
    for capture in captures:
        capture.start()

    # Mantém o programa em execução e para as capturas quando interrompido
    try:
        while True:
            time.sleep(1)  

    except KeyboardInterrupt:
        print("Encerrando capturas...")
        for capture in captures:
            capture.stop()


def main():
    # Inicia o cliente mock
    mock_cliente() 

if __name__ == "__main__":
    main()
