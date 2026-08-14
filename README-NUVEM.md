# ☁️ Migrando o PigeonMaster para a nuvem (Supabase)

A partir da versão **2.2**, o banco de dados do sistema deixa de ficar só no
navegador (`localStorage`) e passa a ficar na **nuvem (Supabase)**.

**O que muda na prática:**

| Antes | Agora |
|---|---|
| Dados só no navegador de 1 computador | Dados na nuvem, acessíveis de qualquer PC |
| Backup manual em arquivo (única proteção) | Cópia automática na nuvem a cada salvamento |
| Trocar de PC = exportar/importar backup | Abrir o sistema em outro PC e pronto |
| 1 pessoa por vez | **Vários PCs ao mesmo tempo, em tempo real** |
| Perdeu o navegador, perdeu tudo | Basta conectar outro PC na nuvem e baixar tudo |

O sistema **continua funcionando sem internet**: ele salva localmente e envia
as pendências para a nuvem assim que a conexão voltar. O backup em arquivo
(menu 💾 Backup) continua existindo e recomendado.

---

## Passo a passo (faz uma vez só, ~10 minutos)

### 1. Criar a conta e o projeto no Supabase (grátis)

1. Acesse **https://supabase.com** e clique em **Start your project**
2. Crie a conta (pode entrar com GitHub, Google ou e-mail)
3. Clique em **New project** e preencha:
   - **Name**: `PigeonMaster` (ou `Clube Limeira`)
   - **Database Password**: crie uma senha e **guarde** (só para administração)
   - **Region**: `South America (São Paulo)` — se aparecer na lista
4. Aguarde ~2 minutos enquanto o projeto é provisionado

### 2. Criar a tabela do sistema

1. No menu lateral do Supabase, clique em **SQL Editor** (ícone `</>`)
2. Clique em **New query**
3. Abra o arquivo **`supabase-setup.sql`** (está nesta pasta), copie TODO o
   conteúdo, cole no editor e clique em **Run**
4. Deve aparecer "Success. No rows returned" — é isso mesmo ✅

> Essa tabela guarda os dados das DUAS versões do sistema separadamente:
> o `index.html` usa o banco `sgc` e o `regional.html` usa o banco `reg`.
> Um único projeto Supabase atende os dois.

### 3. Pegar as chaves de conexão

1. No menu lateral, clique na **engrenagem (Project Settings)**
2. Clique em **API** (ou "Data API")
3. Copie estes dois valores:
   - **Project URL** → algo como `https://abcdefgh1234.supabase.co`
   - **Chave pública** → dependendo da tela, pode ter um destes dois formatos
     (qualquer um dos dois funciona):
     - **Publishable key** → começa com `sb_publishable_...` *(formato novo)*
     - **anon public key** → começa com `eyJ...` *(formato antigo, na aba "Legacy")*

> 🚫 **NUNCA** use a chave `sb_secret_...` (ou "service_role")! Ela é o acesso
> mestre do banco e não pode ficar salva em navegador nenhum. O sistema
> bloqueia colar essa chave por acidente.

### 4. Conectar o PRIMEIRO computador (o que tem os dados hoje)

> ⚠️ **Faça isto primeiro no computador onde os dados do clube estão salvos**,
> para que eles SUBAM para a nuvem.

1. Abra o `index.html` atualizado (versão 2.2) **nesse computador**
2. Clique no novo menu **☁️ Nuvem → 🔧 Configurar conexão...**
3. Cole a **Project URL** e a **chave anon public** → **Salvar e conectar**
4. Deve aparecer: *"✅ Conectado! Os dados foram sincronizados..."*
   — neste momento, os dados locais **subiram** para a nuvem 🎉
5. Repita para o `regional.html`, se você usa as duas versões

### 5. Conectar os OUTROS computadores

1. Copie os arquivos atualizados para o outro PC (ou abra pelo GitHub Pages)
2. Menu **☁️ Nuvem → 🔧 Configurar conexão...** → cole as mesmas URL e chave
3. Como a nuvem já tem dados, eles **descem automaticamente** para esse PC
4. Pronto: a partir daí, o que um PC salvar aparece nos outros em tempo real

---

## Como saber se está funcionando

No **canto inferior direito** da tela aparece o indicador da nuvem:

| Indicador | Significado |
|---|---|
| `☁️ online` | Conectado e sincronizado |
| `☁️ ↑ enviando...` | Enviando alterações para a nuvem |
| `☁️ ↓ atualizado` | Acabaram de chegar dados de outro PC |
| `☁️ offline — salvando aqui` | Sem internet/nuvem: salvando local, envia depois |
| `☁️ modo local` | Nuvem ainda não configurada neste PC |

Clique no indicador para ver o **status detalhado** (pendências, ID do PC etc.).

## Menu ☁️ Nuvem

- **🔧 Configurar conexão...** — colar URL e chave do Supabase
- **📶 Status da sincronização** — estado atual e pendências
- **⬆️ Enviar tudo para a nuvem agora** — força subir os dados deste PC
- **⬇️ Baixar tudo da nuvem agora** — força baixar (substitui os dados daqui)
- **🔌 Desconectar este computador** — volta a trabalhar só no modo local

## Perguntas frequentes

**Dois PCs digitando ao mesmo tempo, e aí?**
Se os dois mexerem na MESMA gaveta ao mesmo tempo, quem salvar por último
prevalece naquela gaveta. Na prática, com o PC do clube lançando e os outros
consultando, não há conflito. Se chegarem lançamentos de outro PC enquanto
você está no meio de um lançamento, o sistema **não atrapalha sua digitação**:
aparece um aviso amarelo embaixo e você aplica quando terminar.

**E se acabar a internet no meio da prova?**
Nada se perde: o sistema salva no computador normalmente e envia tudo para a
nuvem sozinho quando a internet voltar.

**A chave anon é segura?**
Ela é a chave pública padrão de apps Supabase. Quem tiver a URL + chave consegue
ler/gravar os dados do clube, então: **não publique a chave** (não suba no
GitHub, não mande em grupo aberto). Ela fica salva apenas no `localStorage`
dos computadores autorizados. O arquivo no GitHub **não** contém nenhuma chave.

**Quanto custa?**
O plano **gratuito** do Supabase (500 MB de banco + realtime) é mais do que
suficiente para todos os cadastros e lançamentos do clube por muitos anos.

**Preciso refazer isso para o regional.html?**
A tabela é a mesma (passo 2 faz uma vez só). Só o passo 4/5 (colar as chaves)
precisa ser feito em cada arquivo/versão que você usar.

---

## Para enviar esta atualização ao GitHub

```bash
cd PigeonMasterLimeira
git add index.html regional.html supabase-setup.sql README-NUVEM.md apply_cloud_patch.py
git commit -m "v2.2: banco de dados na nuvem (Supabase) com sincronização em tempo real"
git push
```

> O arquivo `apply_cloud_patch.py` é o script que aplicou as alterações.
> Ele não é necessário para o sistema funcionar — fica no repositório apenas
> como documentação do que foi mudado (pode ser apagado, se preferir).
