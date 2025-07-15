from ultralytics import YOLO
"""
Classe PPE para detecção e verificação do uso de Equipamentos de Proteção Individual (EPI) utilizando um modelo YOLO.
Atributos:
    model (YOLO): O modelo YOLO utilizado para detecção.
Métodos:
    __init__(self, model):
        Inicializa a classe PPE com um modelo YOLO fornecido.
    is_inside(self, box1, box2):
        Verifica se o centro da box1 está dentro da box2.
        Args:
            box1 (list): [x, y, w, h] da primeira caixa.
            box2 (list): [x, y, w, h] da segunda caixa.
        Retorna:
            bool: True se box1 está dentro de box2, False caso contrário.
    Iou(self, box1, box2):
        Calcula a Interseção sobre União (IoU) entre duas caixas delimitadoras.
        Args:
            box1 (list): [x1, y1, x2, y2] da primeira caixa.
            box2 (list): [x1, y1, x2, y2] da segunda caixa.
        Retorna:
            float: Valor do IoU.
    get_max(self, objs, Boxes):
        Encontra o objeto com maior score de confiança em uma lista de objetos.
        Args:
            objs (list): Lista de índices dos objetos.
            Boxes: Objeto de caixas detectadas com confiança e coordenadas.
        Retorna:
            tuple: (maior_confiança, caixa_delimitadora)
    using(self, use, no_use, Boxes):
        Determina se um EPI está sendo utilizado com base nos objetos detectados.
        Args:
            use (list): Índices dos objetos onde o EPI está sendo usado.
            no_use (list): Índices dos objetos onde o EPI não está sendo usado.
            Boxes: Objeto de caixas detectadas.
        Retorna:
            tuple: (status, bbox_use, bbox_no_use)
    uses(self, PPEs, Boxes):
        Verifica o status de uso para todas as categorias de EPI (capacete, colete, óculos, luvas, botas).
        Args:
            PPEs (dict): Dicionário mapeando índices de classes de EPI para índices de objetos detectados.
            Boxes: Objeto de caixas detectadas.
        Retorna:
            list: Status de uso de EPI para cada categoria.
    check_ppe(self, PPEs, Boxes):
        Agrega o status de uso de EPI para um conjunto de objetos EPI detectados.
        Args:
            PPEs (list): Lista de índices de objetos EPI detectados.
            Boxes: Objeto de caixas detectadas.
        Retorna:
            list: Status de uso de EPI para cada categoria.
    check(self, people, ppe, Boxes):
        Associa EPI detectado com pessoas detectadas e verifica conformidade.
        Args:
            people (list): Índices das pessoas detectadas.
            ppe (list): Índices dos EPIs detectados.
            Boxes: Objeto de caixas detectadas.
        Retorna:
            list: Lista de status para cada pessoa, incluindo caixa delimitadora e status dos EPIs.
    all_safe(status):
        Verifica se todas as pessoas detectadas estão em conformidade com os EPIs.
        Args:
            status (list): Lista de status de EPI para cada pessoa.
        Retorna:
            bool: True se todos estão em conformidade, False caso contrário.
    inner(self, frame):
        Executa a predição do modelo YOLO em um frame.
        Args:
            frame: Imagem/frame de entrada.
        Retorna:
            Resultado da predição do YOLO.
    run(self, frame):
        Executa todo o pipeline de detecção de EPI e verificação de conformidade em um frame.
        Args:
            frame: Imagem/frame de entrada.
        Retorna:
            list: Status de conformidade de EPI para cada pessoa detectada.
"""

class PPE():
    def __init__(self,model):
        self.model = YOLO(model)


    def is_inside(self, box1, box2):
    
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        x_lim_min = x2 - w2/2
        x_lim_max = x2 + w2/2
        y_lim_min = y2 - h2/2
        y_lim_max = y2 + h2/2
        
        if x_lim_min < x1 <x_lim_max and y_lim_min < y1 < y_lim_max:
            return True
        return False
    
    def Iou(self, box1, box2):
        x_left = max(box1[0], box2[0])
        y_top = min(box1[1], box2[1])
        x_right = min(box1[2], box2[2])
        y_bottom = max(box1[3], box2[3])

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)

        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

        union_area = box1_area + box2_area - intersection_area

        try:
            iou = intersection_area / union_area
        except:
            iou = 0

        return iou
    
    def get_max(self,objs,Boxes):
        maxi = objs[0]

        for i in objs[1:]:
            if Boxes.conf[i] > Boxes.conf[maxi]:
                maxi = objs[i]
        return float(Boxes.conf[maxi]),list(map(int,(Boxes.xyxy[maxi])))
    
    def using(self,use,no_use,Boxes):
        if not use and not no_use:
            return 'unknown',0,0
        if not no_use:
            return True, self.get_max(use,Boxes)[1],0
        if not use:
            return False, 0, self.get_max(no_use, Boxes)[1]
        max_use,bbox_use = self.get_max(use, Boxes)
        max_no_use,bbox_no_use = self.get_max(no_use, Boxes)

        if max_no_use > max_use:
            return False,bbox_use,bbox_no_use
        return True,bbox_use,bbox_no_use

    def uses(self, PPEs, Boxes):
        use_ppe = []

        #helmet
        use_ppe.append(self.using(PPEs[1],PPEs[2],Boxes))
        #vest
        use_ppe.append(self.using(PPEs[3],PPEs[4],Boxes))
        #glasses
        use_ppe.append(self.using(PPEs[5],PPEs[6],Boxes))
        #gloves
        use_ppe.append(self.using(PPEs[7],PPEs[8],Boxes))
        #boots
        use_ppe.append(self.using(PPEs[9],PPEs[10],Boxes))

        return use_ppe



    def check_ppe(self, PPEs, Boxes):
    
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
        for p in PPEs:
            cls = int(Boxes.cls[p])
            dict[cls].append(p)
        return self.uses(dict, Boxes)
            
            

    def check(self, people, ppe, Boxes):
        personal_ppe = []
        status = []

        for p in people:
            person_bbox = list(map(int,Boxes.xywh[p]))
            _ppe = []
            for e in ppe:
                ppe_bbox = list(map(int,Boxes.xywh[e]))

                iou = self.Iou(ppe_bbox, person_bbox)

                if self.is_inside(ppe_bbox, person_bbox):
                    _ppe.append(e)
            status.append([list(map(int,Boxes.xyxy[p])),self.check_ppe(_ppe, Boxes)])
        return status
        

    def all_safe(status):
        for i in status:
            if i[0] != True:
                return False
        return True

    def inner(self, frame):
        resp = self.model.predict(frame,verbose=False)[0]
        return resp

    def run(self, frame):
        resp = self.inner(frame)
        people = []
        ppe = []

        for i,r in enumerate(resp.boxes.cls):
            if int(r) == 0:
                people.append(i)
            else:
                ppe.append(i)
        
        status = self.check(people,ppe,resp.boxes)
        return status

  


                

