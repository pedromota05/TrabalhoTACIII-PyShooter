# Decisões — PyShooter

| Data | Decisão | Por quê |
| :--- | :--- | :--- |
| 2026-11-12 | Sincronização de dano por IDs determinísticos (`target_id`) e pacotes `hit` via UDP | Garante que inimigos e bosses sofram dano e reproduzam a animação de morte simultaneamente em ambas as telas, eliminando descompassos no multiplayer. |
| 2026-11-21 | Regras de vida: modo normal = 3 vidas compartilhadas, aviso "-1 VIDA" e renascer sozinho, sem vidas = GAME OVER (1 jogador: Restart recomeça a fase; dupla: espera e o Host recomeça). Desafio = uma vida por jogador, sem checkpoints, cronômetro no HUD; em dupla quem cai assiste, volta na fase seguinte com metade da vida, e os dois caídos encerram o Desafio (Host recomeça da fase 1). | O Desafio em dupla não tinha regra e caía na tela de Restart do modo normal; a regra mantém o "uma vida só" sem tirar o parceiro do jogo à toa. |
