# 🐦 Correções Aplicadas — PigeonMaster v2.3

Data: 26/08/2026
Arquivos corrigidos: `index.html` e `regional.html`
Backups: `index.html.bak` e `regional.html.bak` (originais, antes da correção)

---

## 🐛 Bug 1 — Tempo morto do concurso dava negativo no lançamento

### Causa real
O sistema copiava **cegamente** o campo `tm1` (1ª noite) do concurso para o campo
"Tempo Morto" de **TODO lançamento**, inclusive pombos que chegaram no mesmo dia
(`Dias = 1`, sem passar nenhuma noite). Se a 1ª noite estava cadastrada como
12h00 e um pombo voou 4h, o cálculo era:

```
chegada (4h) − partida (0h) − tempo morto (12h) = −8h  →  negativo!
```

Daí o sistema forçava pra zero e a média ficava 0 — exatamente o que você viu.
Quando você apagava do concurso e digitava manualmente, o bug sumia porque o
campo ficava em 00:00 para os pombos do mesmo dia.

### Correção aplicada
- O tempo morto agora é calculado **automaticamente** conforme o nº de
  **noites reais** que o pombo levou:

  | Dias | Noites | Tempo Morto aplicado |
  |------|--------|----------------------|
  | 1 (mesmo dia) | 0 | `00:00:00` |
  | 2 | 1 | `tm1` |
  | 3 | 2 | `tm1 + tm2` |
  | 4+ | 3 | `tm1 + tm2 + tm3` |

- Se você quiser sobrescrever manualmente (clicar e digitar), o sistema
  respeita — igual você fazia antes. Ao trocar de pombo ou selecionar nova
  prova, volta ao automático.
- Corrigido também na **importação do GPC** e na **importação PMR**: antes
  também colavam `tm1` em todos os lançamentos.
- Corrigido também o **cálculo oficial**: ele detecta automaticamente
  lançamentos antigos (feitos antes da correção) que tenham tMorto indevido
  para pombo do mesmo dia e zera o tempo morto na hora de calcular, sem
  exigir que você reabra um por um.
- Campos **Data Inicial**, **Data Final** e **Hora Fim** agora também
  disparam o recálculo automático (antes era preciso dar tab para atualizar).
- Se por acaso o tempo continuar negativo (chegada anterior à partida por
  erro de digitação), o campo "Tempo voo" fica **vermelho** em vez de azul,
  chamando atenção pra conferir.

---

## 📱 Dúvida 2 — Link PMR: pombo do dia + pombo do dia seguinte

### Como o app do sócio se comporta HOJE (sem correção)
O app do celular **não sabe** se um pombo chegou no mesmo dia ou na madrugada
do dia seguinte. Ele simplesmente registra:
- A hora da constatação (ex: 11:34 para pombos do dia, 05:30 para pombos de
  madrugada)
- As observações que o sócio digitar (ex: "chegou dia seguinte")
- Tudo vai no mesmo arquivo `.PMR`, misturado.

Na importação, **todos os pombos entram como `Dias=1`** (mesmo dia), e os
pombos da madrugada vão dar tempo de voo negativo/zerado até que você ajuste
manualmente o `Dias` para 2 e confira a data final.

### Melhorias que adicionei
1. **Aviso no app do sócio**: agora aparece uma caixinha amarela pedindo que
   ele marque na observação se algum pombo chegou no dia seguinte — isso
   ajuda você a identificar na hora de importar.
2. **Na importação PMR**: os pombos são criados com `tMorto = 00:00:00`
   (em vez de já virem com `tm1` errado) — assim, pombos do dia não ficam
   com tempo negativo logo de cara. Você ajusta o Dias=2 e o tempo morto
   é aplicado automaticamente pela correção do Bug 1.

### Como proceder na prática (pra lembrar)
1. Importa o `.PMR` do sócio.
2. Vai na lista de lançamentos da prova.
3. Para os pombos de madrugada (dia seguinte):
   - Dê um duplo-clique no pombo na lista da **Auditoria PMR** (ou clique
     em Editar na lista de lançamentos),
   - Ajuste `Data Final` para o dia seguinte,
   - Ajuste `Dias +` para `2`,
   - O tempo morto vai ser preenchido com `tm1` automaticamente ✅,
   - Salve.
4. Os pombos do dia (Dias=1) já estarão corretos, sem tempo morto.

---

## 📤 Como enviar esta correção pro GitHub

Do seu computador, dentro da pasta `PigeonMasterLimeira`:

```bash
cd PigeonMasterLimeira

# Ver o que mudou
git status
git diff --stat

# Adicionar os arquivos corrigidos
git add index.html regional.html

# Commitar
git commit -m "v2.3: corrige bug do tempo morto negativo + melhorias no PMR

- Tempo morto agora é calculado automaticamente pelo nº de noites
  (dias=1: 00h; dias=2: tm1; dias=3: tm1+tm2; dias=4+: tm1+tm2+tm3),
  em vez de copiar tm1 cegamente para todos os lançamentos.
- Corrigido na tela de lançamento, no cálculo oficial e nas importações
  GPC/PMR — incluindo detecção de lançamentos antigos com tMorto indevido.
- Campos Data Ini/Fim e Hora Fim agora recalculam em tempo real.
- Operador pode sobrescrever manualmente o tempo morto (respeitado).
- Aviso no app do sócio (PMR) sobre pombos do dia seguinte.
- Versão 2.3."

# Enviar pro GitHub
git push
```

Se quiser testar antes de publicar, os arquivos já estão abertos aqui em
`/home/user/PigeonMasterLimeira/index.html` e `regional.html` (servidor
HTTP rodando na porta 8080 desta máquina).

---

## ⚠️ Aviso importante sobre a v2.2 vs v2.3 com a nuvem
Esta correção mexe APENAS no cálculo em tempo real na tela e na importação.
Ela **não apaga** nenhum dado existente. Ao rodar o Cálculo de Prova depois
de atualizar, o próprio sistema corrige automaticamente os lançamentos
antigos que tinham sido salvos com tempo morto indevido para pombos do
mesmo dia.

Se você tiver provas já **confirmadas** (salvas em Classificações) antes
desta correção e quiser que o resultado reflita o tempo correto, basta
abrir "Cálculo de Prova", selecionar a prova, mandar Confirmar de novo e
depois Confirmar Resultado — os tempos serão recalculados.

---

## 🐛 Correção extra (26/08/2026) — Tela do PMR abrindo com pombo pré-preenchido

**Problema relatado:** "essa tela tem que estar vazia!!! esse pombo com horario não deve aparecer ali!!!"

A tela do PigeonMaster Remote Clock (PMR — a telinha que simula o app do celular do sócio) estava vindo de fábrica com **valores de demonstração hardcoded no HTML**:
- Anilha: `2335027/23` (já escrita no campo)
- Hora da constatação: `11:34:58` (já escrita no campo)
- Cabeçalho: "Conc 1/2026 - Prova Igarapava" / "81 - VILMAR ALMEIDA PORTA DO SOL" / "Benzing" / "GPS: -22.561100, -47.382500"

Esses valores eram só um exemplo visual do programador, mas apareciam como se fossem um pombo já cadastrado — confundia o operador.

**Correção aplicada (index.html e regional.html):**
1. Removidos todos os `value="..."` de demonstração dos inputs do celular. Agora os campos de anilha, hora e observações abrem **vazios**.
2. Cabeçalho (Sócio / Concurso / Relógio / GPS) agora mostra "—" ou "Capturando localização..." até que os dados sejam carregados por link PMR real.
3. Função `abrirTelaCelularSocio()` foi reforçada para **sempre limpar** anilha/hora/obs ao abrir a janela, focar automaticamente no campo de anilha, e resetar a lista `pmrAnilhasMobile` antes de carregar rascunho (evita "lixo" de uma sessão anterior aparecer).
4. O botão ⏰ Exata continua funcionando para o sócio capturar a hora do celular quando precisar.

**Importante:** quando um link PMR real é aberto no celular (pelo WhatsApp), a função `initPMRFromUrl()` sobrescreve esses valores corretamente — o nome do sócio e o concurso aparecem normalmente.

---

## 🐛 Correção extra 2 (26/08/2026) — Lista de conferência PMR sumia depois da apuração

**Problema relatado:** "quando eu importo o pmr ele gera uma lista de conferencia para homologar correto? mas se eu fizer a apuração provisoria a lista apaga!!! ela teria que ficar ate na semana seguinte para conferencia e homologação"

**Causa raiz:** A tabela da aba "Auditoria & Homologação" usava a variável global `lancamentos`, que só contém os lançamentos da prova **que estiver aberta na tela de Lançamento naquele momento**. Quando o operador:
- Troca de concurso em Lançamento,
- Fecha/abre janelas depois da apuração,
- Roda o cálculo provisório,

o array global `lancamentos` pode apontar para outra prova (ou ficar vazio), e a lista de pombos PMR parece ter "sumido" — embora os dados ainda estivessem gravados no localStorage, só que a auditoria olhava no lugar errado.

Além disso, `executarCalculo()` atualizava distância e média dos lançamentos em memória mas **não chamava `salvarLancamentos()` no final** — se fechasse o app, os dados calculados se perdiam.

**Correção aplicada (index.html e regional.html):**
1. `atualizarTabelaAuditoriaPMR()` agora busca os lançamentos DIRETAMENTE pela chave `ano/num` selecionada na tela do PMR (`todosLancamentos[chavePMR]`), independente de qual prova esteja aberta em outra janela.
2. `registrarHoraFisicaPMR()`, `homologarConstatacaoIndividual()` e `homologarTodosExatos()` também trabalham em cima do array da prova do PMR, e salvam direto no localStorage (não dependem mais da variável global `lancamentos`).
3. Contador agora mostra também quantos já foram homologados, e o texto diz explicitamente que a lista fica salva até a homologação.
4. `executarCalculo()` agora chama `salvarLancamentos()` no final, garantindo que distâncias e médias fiquem persistidas em disco para a conferência da semana seguinte.
5. Quando a prova aberta em Lançamento é a mesma do PMR, a sincronização em memória continua funcionando (pra lista da tela de Lançamento também refletir as homologações).

**Resultado:** O operador pode: importar o PMR → lançar provisório → rodar a apuração provisória → fechar o app → abrir no dia/na semana seguinte → a lista de auditoria continua lá inteira, com os mesmos pombos e status, pronta para a homologação oficial contra os relógios físicos.

---

## 🐛 Correção extra 3 (26/08/2026) — Link PMR no celular do sócio pedia chaves do banco

**Problema relatado:** "quando eu mandava o link pmr para o socio ele tinha que por as chaves do banco eles não tem acesso!!!"

**Causa raiz:** Ao abrir o link `?pmr=1` no celular, o sistema inicializava como se fosse o computador do clube — carregava todo o desktop Windows 3.11 com menus, barra de ferramentas, lembrete de backup, e acionava o popup "☁️ Deseja configurar a nuvem (Supabase) agora?". Se o sócio clicasse OK sem querer, ele ia parar numa tela pedindo Project URL e chave anônima do Supabase (que ele não tem nem deve ter).

**Correção aplicada (index.html e regional.html):**

1. **Modo "celular do sócio" (`entrarModoPmrCelular()`)**: quando a URL tem `?pmr=1`, o sistema automaticamente:
   - **Oculta 100% da interface desktop** (menus, janelas, barra de status, lembrete de backup)
   - Mostra **apenas a telinha do PMR** em tela cheia, limpa
   - **NÃO** oferece configuração de nuvem nem pede chaves de banco
   - **NÃO** carrega lembrete de backup
   - O botão ✖ do topo agora fecha a constatação de forma segura (pergunta antes, e mostra tela de encerramento)
   - O reloginho do topo (que estava travado em "11:34" de exemplo) agora mostra a hora REAL do aparelho do sócio, atualizada a cada 30 segundos.
   - O título da aba do navegador muda para "PigeonMaster - Constatação Remota"

2. **Função `cloudOferecerConfigInicial()`** agora retorna imediatamente se detectar `pmr=1` na URL — sem perguntar nada sobre Supabase para quem é sócio.

3. **CSS específico** (`.pmr-mobile-mode`) garante que mesmo se algum elemento tentar aparecer, ele fica oculto no celular do sócio.

**Resultado:** O sócio clica no link do WhatsApp → abre direto na telinha limpa com nome dele e do concurso → só precisa digitar anilhas, conferir hora, gerar .PMR e enviar. Não aparece menu, não aparece pergunta sobre banco, não aparece nada de configuração — experiência 100% simples para quem não entende de informática.

---

## 🆕 Correções v2.3.1 — Nuvem (Supabase) mais robusta

**Problemas que causavam "a nuvem parou de funcionar":**
1. A biblioteca do Supabase era carregada de UM ÚNICO CDN (jsdelivr.net). Se esse site estivesse lento/bloqueado na internet do clube (muito comum em redes corporativas, 4G ou antivírus), a nuvem falhava silenciosamente, mesmo com as chaves corretas salvas.
2. O sistema tentava sincronizar logo no carregamento, sem esperar a biblioteca carregar.
3. Não havia mensagem clara do motivo da falha (hibernação, chave errada, sem internet, tabela faltando).
4. Erros de rede só tentavam novamente em 15s (muito frequente) e não explicavam o motivo.

**Correções aplicadas (tanto `index.html` quanto `regional.html`):**
- Carregamento com **4 CDNs de fallback** (jsdelivr → unpkg → cdnjs → esm.sh): se um falhar, tenta o próximo automaticamente.
- O sistema **espera até 6 segundos** a biblioteca carregar antes de desistir da nuvem (evita falso "offline" em internet lenta).
- Cliente Supabase criado com `auth.persistSession: false` (economiza armazenamento e evita ruído).
- Classificação de erros em português claro, com dica do que fazer (projeto hibernado → abrir painel do Supabase; chave inválida → recopiar; tabela faltando → rodar SQL).
- Status da nuvem (canto inferior direito) agora mostra **o motivo exato** de estar offline quando você clica nele.
- Retentativa de envio em 30s (em vez de 15s, evita excesso de tentativas).
- Mensagens de erro amigáveis em português.

**Se a nuvem aparecer offline:**
1. Clique no indicador ☁️ no canto inferior direito → ele dirá o motivo exato.
2. O motivo MAIS COMUM é o **projeto Supabase hibernado** (plano grátis dorme após 7 dias sem uso): basta entrar no painel do Supabase e abrir o projeto que ele acorda em 30 segundos.
3. O sistema continua funcionando 100% no modo local mesmo sem nuvem — os dados ficam salvos no computador.
