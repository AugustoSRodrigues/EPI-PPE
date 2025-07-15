# Detecção de Uso de EPI (Equipamento de Proteção Individual)

## Intro

Este projeto tem como objetivo detectar automaticamente, por meio de visão computacional, o uso correto de Equipamentos de Proteção Individual (EPI) em ambientes industriais ou de construção. Utilizando modelos de deep learning, o sistema processa vídeos ou imagens e identifica se as pessoas estão utilizando os EPIs obrigatórios.

O modelo foi treinado com um dataset próprio, composto por imagens coletadas em cenários reais de uso de EPIs.

Atualmente, o sistema é capaz de detectar os seguintes itens de segurança:

- Capacete
- Colete
- Óculos de proteção
- Luvas
- Botas

Novos tipos de EPI podem ser adicionados conforme a evolução do projeto.

## Exibição

Abaixo estão exemplos do funcionamento do sistema:

### Detecção Correta de EPI
![EPI Correto](midia/ppe_certo.gif)

### Detecção de Violação de EPI
![Violação de EPI](midia/ppe_violacao.gif)


## TODO

- Integrar o sistema com o bot do Telegram para envio de notificações automáticas.
- Remover trechos de código hard-coded, tornando o projeto mais configurável e flexível.