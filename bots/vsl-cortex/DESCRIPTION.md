# VSL Cortex (7fe4a5a1-845c-494d-9fc2-93986c8ef6ea)

Versão: antes (lifecycle 2026-11-15)

Recebe VSLs longas (até 1 GB) e transforma em criativos curtos pra anúncios. Fluxo: 1) transcreve o vídeo com Whisper; 2) mapeia ganchos, momentos de pico e picos de retenção; 3) devolve uma lista de cortes com timestamps para os formatos 9:16, 1:1 e 4:5, com sugestão de legenda queimada e CTA; 4) espera aprovação do Wagner antes de renderizar com ffmpeg. Nunca sobrescreve o arquivo original. Preferências (loudness, pasta de saída, estilo de legenda) são perguntadas na primeira execução e guardadas. Não posta nada em lugar nenhum. Não faz motion graphics nem color grading.
