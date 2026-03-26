# RideFleet

Este projeto consiste no desenvolvimento do RideFleet, um sistema de transporte por aplicativo inspirado em plataformas como Uber, 99 e Lyft. A proposta é simular, na prática, os desafios enfrentados por esse tipo de aplicação, principalmente no contexto de sistemas distribuídos. Cada grupo da turma, formado por quatro integrantes, é responsável por criar seu próprio serviço de gerenciamento de corridas, cuidando de todo o fluxo da aplicação.

Além disso, o projeto envolve uma parte colaborativa importante: um integrante de cada grupo participa do desenvolvimento de um núcleo compartilhado, responsável pela comunicação entre os diferentes serviços. Esse núcleo permite que, quando um sistema estiver sobrecarregado ou indisponível, ele consiga repassar corridas para outro grupo, criando um ambiente distribuído mais realista, onde vários sistemas independentes precisam cooperar.

Com essa dinâmica, surgem desafios clássicos de sistemas distribuídos, como garantir que uma mesma corrida não seja aceita por mais de um motorista, manter a consistência dos dados entre serviços diferentes e lidar com falhas sem interromper o sistema. Para isso, são utilizados conceitos como travas distribuídas, protocolos de commit, consenso, detecção de falhas e ordenação de eventos, que também devem ser compreendidos e demonstrados ao longo do projeto.
