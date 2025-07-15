import cv2
import os
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont
import numpy as np
def is_inside(box1,box2):
    '''Verifica se um bbox esta dentro do outro
    
    Parametros:
            box1(list): Bbox no formato (x,y,w,h)
            box2(list): Bbox no formato (x,y,w,h)
            
    Return(boll): True se box1 está dentro de box2, False caso contrário'''
    
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    
    x_lim_min = x2 - w2/2
    x_lim_max = x2 + w2/2
    y_lim_min = y2 - h2/2
    y_lim_max = y2 + h2/2
    
    if x_lim_min < x1 <x_lim_max and y_lim_min < y1 < y_lim_max:
        return True
    return False

def Iou(box1,box2):
    x_left = max(box1[0], box2[0])
    y_top = min(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = max(box1[3], box2[3])

    # Se não houver interseção
    if x_right < x_left or y_bottom < y_top:
        return 0.0

    # Área da interseção
    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # Área das duas caixas
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    # Área da união
    union_area = box1_area + box2_area - intersection_area

    # Calcular IoU
    try:
        iou = intersection_area / union_area
    except:
        iou = 0

    return iou

def get_max(objs,Boxes):
    maxi = objs[0]

    for i in objs[1:]:
        if Boxes.conf[i] > Boxes.conf[maxi]:
            maxi = objs[i]
    return Boxes.conf[maxi]

def all_safe(status):
    for i in status:
        if i[0] != True:
            return False
    return True

def draw(frame,bbox,status):
    

    ppe_name = {0:'Capacete',
                1:'Veste',
                2:'Oculos',
                3:'Luvas',
                4:'Calcados'}
    x1,y1,x2,y2 = map(int,bbox)
    if all_safe(status):
        frame = cv2.rectangle(frame,(x1,y1),(x2,y2),color=(0,255,0))
        #frame = cv2.putText(frame,'Save',(x2+10,y1),cv2.FONT_HERSHEY_SIMPLEX,fontScale=1,color=(0,255,0))
    else:
        frame = cv2.rectangle(frame,(x1,y1),(x2,y2),color=(0,0,255))
        #frame = cv2.putText(frame,'Unsave',(x2+10,y1),cv2.FONT_HERSHEY_SIMPLEX,fontScale=1,color=(0,0,255))
    shit = 40
    # pil_img = Image.fromarray(frame)
    # draw = ImageDraw.Draw(pil_img)
    # font = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
    # font = ImageFont.truetype("arial.ttf", 40)
    for i,s in enumerate(status):
            color = (0,255,0)  if s[0]==True  else (0,0,255) if s[0] == False else (128,128,128)
            txt =  'Usando' if s[0]==True  else 'Nao Usando' if s[0] == False else 'Desconhecido'
            # draw.text((x1+10,y1+shit),str(ppe_name[i])+': ' +txt + f' {s[1]:.2f} {s[2]:.2f}',font=font, fill=color)
            frame = cv2.putText(frame,str(ppe_name[i])+': ' +txt + f' {s[1]:.2f} {s[2]:.2f}' ,(x1+10,y1+shit),cv2.FONT_HERSHEY_SIMPLEX,fontScale=1.5,color=color,thickness = 2)
            shit+=40
    # frame = np.array(pil_img)




def using(use,no_use,Boxes):
    if not use and not no_use:
        return 'unknown',0,0
    if not no_use:
        return True, get_max(use,Boxes),0
    if not use:
        return False, 0, get_max(no_use,Boxes)
    max_use =  get_max(use,Boxes)
    max_no_use = get_max(no_use,Boxes)

    if max_no_use > max_use:
        return False,max_use,max_no_use
    return True,max_use,max_no_use

def uses(PPEs,Boxes):
    use_ppe = []

    #helmet
    use_ppe.append(using(PPEs[1],PPEs[2],Boxes))
    #vest
    use_ppe.append(using(PPEs[3],PPEs[4],Boxes))
    #glasses
    use_ppe.append(using(PPEs[5],PPEs[6],Boxes))
    #gloves
    use_ppe.append(using(PPEs[7],PPEs[8],Boxes))
    #boots
    use_ppe.append(using(PPEs[9],PPEs[10],Boxes))

    return use_ppe



def check_ppe(PPEs,Boxes):
   
    dict = {1:[],
            2:[],
            3:[],
            4:[],
            5:[],
            6:[],
            7:[],
            8:[],
            9:[],
            10:[]
        }
    # if PPEs[0]:
    for p in PPEs:
        cls = int(Boxes.cls[p])
        dict[cls].append(p)
    return uses(dict,Boxes)
        
        

def check(people,ppe,Boxes):
    personal_ppe = []
    status = []

    for p in people:
        person_bbox = list(map(int,Boxes.xywh[p]))
        _ppe = []
        for e in ppe:
            ppe_bbox = list(map(int,Boxes.xywh[e]))

            iou = Iou(ppe_bbox,person_bbox)

            if is_inside(ppe_bbox,person_bbox):
                _ppe.append(e)
        # personal_ppe.append(_ppe)
        status.append(check_ppe(_ppe,Boxes))
    return status
    
    

def main():
    
    model = YOLO('runs/detect/train15/weights/best.pt')
    
    video_path = 'videos_test/8488067-uhd_3840_2160_30fps (1).mp4'
    cap = cv2.VideoCapture(video_path)
 
    
    if not cap.isOpened():
        print("Erro ao abrir o arquivo de vídeo")
        exit()

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))  # Frames por segundo

    # Definir o codec e criar o objeto VideoWriter para salvar o novo vídeo
    output_path = '8488067-uhd_3840_2160_30fps (1)_pt.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec para formato MP4
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    while True:
        ret, frame = cap.read()
        people = []
        ppe = []
        
        if not ret:
            print("Fim do vídeo")
            break
        
        res = model(frame,conf=0.5)[0]

        # for r in res.boxes.xyxy:
            
        #     x1,y1,x2,y2 = map(int,r)
        #     frame = cv2.rectangle(frame,(x1,y1),(x2,y2),color=(0,255,0))

        for i,r in enumerate(res.boxes.cls):
            if int(r) == 0:
                people.append(i)
            else:
                ppe.append(i)
        
        status = check(people,ppe,res.boxes)

        for p,s in zip(people,status):
            draw(frame,res.boxes.xyxy[p],s)

        out.write(frame)
        cv2.namedWindow('Frame',cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Frame', 2480,1440)

        # cv2.imshow('Frame', frame)

        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    
    cap.release()
    cv2.destroyAllWindows()
main()