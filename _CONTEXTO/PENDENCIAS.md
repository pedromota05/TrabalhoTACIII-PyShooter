# PENDENCIAS

Status: A FAZER | EM ANDAMENTO | AGUARDANDO | CONCLUÍDA (AAAA-MM-DD) | CANCELADA (AAAA-MM-DD): motivo. Marcar como concluída em vez de apagar.
Prioridade: Alta | Média | Baixa | vazio = não definida.
Prazo: AAAA-MM-DD, ou texto como "a definir" (fica sem prazo no quadro).
Solicitante, Aguardando, Próximo passo e Ganho h/mês: opcionais, editáveis pelo Trilho (Abrir-Trilho.bat).
Agenda: reunião/conversa marcada, "AAAA-MM-DD HH:MM · com quem / onde" (opcional).
ID: preenchido pelo scripts/pendencias.py do Trilho (<PREFIXO>-<nnn>; o prefixo é o id do projeto em dados/projetos.csv). Não editar à mão.

| ID | Aberta em | Frente | Prioridade | Tarefa | Prazo | Status | Solicitante | Aguardando | Próximo passo | Ganho h/mês | Agenda |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TAC3-001 | 2026-11-12 | Acadêmico | Alta | Terminar de testar tudo e corrigir o multiplayer do PyShooter | 2026-11-14 | EM ANDAMENTO |  |  | Multiplayer corrigido em 2026-11-19 (fase sincronizada, dano em dobro, timeout do morto); tools/teste_multiplayer.py 7/7 OK em 2026-11-19, também pelo IP do Wi-Fi (--ip); falta só o checklist manual em 2 PCs com o Pedro |  |  |
|  | 2026-11-18 | Acadêmico | Alta | Corrigir fim da campanha: fase 4 sem saída/vitória, fase 5 inacessível (MAX_LEVELS), fim volta para fase 3 | a definir | CONCLUÍDA (2026-11-18) |  |  | Vitória ao matar os chefes da fase 4 + tela VITÓRIA; fase 5 vira arena do Desafio (etapa 6) |  |  |
|  | 2026-11-18 | Acadêmico | Alta | Executar o plano de melhorias das fases (C:\Users\guilh\.claude\plans\agile-purring-stonebraker.md): bot de teste, vitória, progresso no menu de fases, checkpoints, edição dos mapas, Modo Desafio e teste do multiplayer | a definir | CONCLUÍDA (2026-11-19) |  |  | Etapas 1 a 7 com código pronto (6 e 7 em 2026-11-19, commits a8983ea e 58e26eb); validadas com pygame em 2026-11-19 |  |  |
|  | 2026-11-18 | Acadêmico | Alta | Preparar a apresentação do PyShooter na aula: entender bem o código, mostrar a gameplay, fazer os slides e explicar o GDD (docs/GDD_Trabalho2.md), que precisa estar atualizado com as mudanças do plano | 2026-11-24 | EM ANDAMENTO |  |  | GDD atualizado, rascunho de 15 slides e guia de estudo (docs/2026-11-19_guia-de-estudo-apresentacao.md) em 2026-11-19; falta Guilherme e Pedro lerem o guia, revisar os slides, capturas no deck e no docs/apresentacao/2026-11-19_slides-pyshooter_v2.pptx em 2026-11-19; falta dividir a fala, ensaiar e o relatório em PDF |  |  |
|  | 2026-11-19 | Acadêmico | Alta | Validar com pygame as etapas 6 e 7: `python tools/bot_fases.py --desafio --capturas docs/capturas` e `python tools/teste_multiplayer.py`; corrigir falhas | 2026-11-22 | CONCLUÍDA (2026-11-19) |  |  | Bot campanha 1-4 OK, Desafio 1-5 OK (--god), teste_multiplayer 7/7 OK após ajustar a medição; bug FASE 6/5 corrigido |  |  |
|  | 2026-11-21 | Acadêmico | Alta | Melhorias do cooperativo: Ctrl+V no IP, itens, colisão, cor, vidas, placas, seleção multiplayer, castelo | 2026-11-24 | CONCLUÍDA (2026-11-21) |  |  | Branch melhorias-coop, testada com bot e teste_multiplayer; falta push e teste real com o Pedro |  |  |
|  | 2026-11-21 | Acadêmico | Média | Entender por que a fase 2 "não terminou" na gameplay (não reproduzido pelo bot) | 2026-11-24 | AGUARDANDO |  | Guilherme descrever o que aconteceu |  |  |  |
|  | 2026-11-21 | Acadêmico | Alta | Mira no mouse + dash, editor (mover, checkpoint, castelo), cor sem repetir, renascer no buraco, chefes em etapas, HUD das vidas | 2026-11-24 | EM ANDAMENTO |  |  | Código pronto e testado pelo bot/teste_multiplayer; falta Guilherme testar na mão e commitar |  |  |
