#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplica a sincronização com a nuvem (Supabase) no PigeonMaster Limeira.
Uso: python3 apply_cloud_patch.py
O script é idempotente: se o patch já estiver aplicado, ele avisa e sai.
"""
import sys

CRLF = "\r\n"

# ---------------------------------------------------------------------------
# CSS dos elementos da nuvem
# ---------------------------------------------------------------------------
CLOUD_CSS = (
    "/* ===== Nuvem (Supabase) ===== */" + CRLF +
    "#cloudStatus{position:fixed;right:6px;bottom:2px;z-index:20001;font-size:11px;font-family:Tahoma,Arial;cursor:pointer;user-select:none;color:#555}" + CRLF +
    "#cloudLoading{position:fixed;left:0;top:0;right:0;bottom:0;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.15);z-index:99999}" + CRLF +
    "#cloudToast{position:fixed;left:50%;transform:translateX(-50%);bottom:26px;z-index:20002;background:#fffbe6;border:1px solid #d8b400;padding:8px 12px;font-size:11px;cursor:pointer;box-shadow:2px 2px 6px rgba(0,0,0,.3);display:none;max-width:92vw}" + CRLF +
    "#cloudModalOverlay{position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(0,0,0,.25);z-index:99998;display:none;align-items:center;justify-content:center}" + CRLF +
    ".cloud-modal{background:#ececec;border:1px solid #555;box-shadow:3px 3px 8px rgba(0,0,0,.4);width:540px;max-width:94vw;font-family:Tahoma,Arial;font-size:11px}" + CRLF +
    ".cloud-modal-title{background:linear-gradient(to bottom,#c9dded,#9fc0dd);padding:5px 8px;font-weight:bold;display:flex;justify-content:space-between}" + CRLF +
    ".cloud-modal-body{padding:10px;line-height:1.5}" + CRLF +
    ".cloud-modal-body input{width:100%;height:24px;margin:2px 0 8px;padding:2px 4px;font-size:11px;border:2px inset #ddd;box-sizing:border-box}" + CRLF +
    ".cloud-modal-btns{display:flex;gap:6px;justify-content:flex-end;padding:0 10px 10px}" + CRLF
)

# ---------------------------------------------------------------------------
# Módulo JavaScript da nuvem (inserido logo após saveLS/loadLS)
# ---------------------------------------------------------------------------
CLOUD_JS = r"""
/* =================== SINCRONIZAÇÃO COM A NUVEM (SUPABASE) ===================
   O banco de dados oficial do clube passa a ser o Supabase (nuvem).
   O localStorage deste navegador continua existindo como CÓPIA LOCAL (cache):
   - tudo que o sistema salva é enviado para a nuvem logo em seguida;
   - ao abrir, o sistema baixa da nuvem os dados mais novos antes de iniciar;
   - com Realtime ligado, o que um computador salvar aparece nos outros
     automaticamente, sem precisar recarregar;
   - sem internet (ou sem configurar), o sistema funciona no modo local e
     envia as pendências quando a conexão voltar.
   Configuração: menu "☁️ Nuvem" → "Configurar conexão...". */
const CLOUD_TABELA = "sgc_store";
const CLOUD_APP_ID = (STORE.pombos || "sgc_pombos").split("_")[0]; /* "sgc" ou "reg" */
const CLOUD_CFG_KEY = CLOUD_APP_ID + "_cloud_config";
const CLOUD_META_KEY = CLOUD_APP_ID + "_cloud_meta";
const CLOUD_DEVICE_KEY = CLOUD_APP_ID + "_cloud_device";
let cloudClient = null, cloudInscricao = null, cloudOnline = false, cloudAppIniciado = false;
let cloudTempoRealOk = false, cloudPollingTimer = null;
let cloudTimers = {}, cloudPendentes = {}, cloudUltimoSync = null;
let cloudRemotoAguardando = {};
let cloudUltimoErro = null;

function cloudCfg() { return loadLS(CLOUD_CFG_KEY, null); }
function cloudSalvarCfg(c) { saveLS(CLOUD_CFG_KEY, c); }
function cloudMeta() { const m = loadLS(CLOUD_META_KEY, { chaves: {} }); if (!m.chaves) m.chaves = {}; return m; }
function cloudSalvarMeta(m) { saveLS(CLOUD_META_KEY, m); }
function cloudDeviceId() {
  let d = localStorage.getItem(CLOUD_DEVICE_KEY);
  if (!d) { d = "pc-" + Math.random().toString(36).slice(2) + Date.now().toString(36); localStorage.setItem(CLOUD_DEVICE_KEY, d); }
  return d;
}
function cloudChavesSincronizadas() {
  const ks = Object.keys(STORE).map(function (k) { return STORE[k]; });
  if (typeof STORE_PMR_LINKS !== "undefined" && ks.indexOf(STORE_PMR_LINKS) < 0) ks.push(STORE_PMR_LINKS);
  return ks;
}
function cloudHabilitada() { const c = cloudCfg(); return !!(c && c.url && c.key && window.supabase); }
function cloudGetClient() {
  if (!cloudHabilitada()) return null;
  if (!cloudClient) {
    const c = cloudCfg();
    try { cloudClient = window.supabase.createClient(cloudNormalizarUrl(c.url), c.key); }
    catch (e) { console.warn("Nuvem: falha ao iniciar cliente", e); return null; }
  }
  return cloudClient;
}
function cloudTs(s) { const n = Date.parse(s || ""); return isNaN(n) ? 0 : n; }
/* Aceita a URL mesmo se colarem com barra ou /rest/v1 no final */
function cloudNormalizarUrl(u) {
  return String(u || "").trim().replace(/\/+$/, "").replace(/\/rest\/v1$/i, "");
}

/* Traduz os erros mais comuns do Supabase para um pt-br que ajuda a resolver */
function cloudTraduzirErro(e) {
  const m = String((e && (e.message || e.error_description || e.hint || e.details)) || e || "");
  const ml = m.toLowerCase();
  if (ml.indexOf("could not find the table") >= 0 || (ml.indexOf("sgc_store") >= 0 && ml.indexOf("does not exist") >= 0))
    return "A tabela ainda nao foi criada no Supabase. Faca a ETAPA 3 do guia: SQL Editor, colar o arquivo supabase-setup.sql, botao Run (tem que aparecer Success em verde).";
  if (ml.indexOf("row-level security") >= 0 || ml.indexOf("row level security") >= 0)
    return "As permissoes da tabela nao foram criadas. Rode o arquivo supabase-setup.sql COMPLETO de novo (ETAPA 3 do guia).";
  if (ml.indexOf("invalid") >= 0 || ml.indexOf("jwt") >= 0 || ml.indexOf("401") >= 0 || ml.indexOf("api key") >= 0)
    return "A URL ou a chave colada parece errada. Copie de novo em: engrenagem (Project Settings), API, no site SUPABASE.COM. A chave certa e a Publishable (sb_publishable_...) ou a anon public (eyJ...) — NAO a sb_secret e NAO as do Firebase!";
  if (ml.indexOf("failed to fetch") >= 0 || ml.indexOf("network") >= 0 || ml.indexOf("name or service") >= 0)
    return "Sem contato com o Supabase. Confira a internet do computador e se a URL colada e do tipo https://...supabase.co (nada de endereco do Firebase).";
  return m;
}
/* Botão 🔎 Testar conexão — diagnóstico guiado, sem precisar abrir console */
async function cloudTestarConexao() {
  const url = cloudNormalizarUrl(document.getElementById("cloudCfgUrl").value);
  const key = document.getElementById("cloudCfgKey").value.trim();
  const out = document.getElementById("cloudTesteResultado");
  if (!/^https:\/\/.+/.test(url) || key.length < 10) { out.innerHTML = "<div style='margin-top:6px'>Preencha a URL e a chave primeiro.</div>"; return; }
  const H = { "apikey": key, "Authorization": "Bearer " + key };
  const linha = function (ok2, txt) { return "<div style='margin-top:6px'>" + (ok2 ? "✅ " : "❌ ") + txt + "</div>"; };
  out.innerHTML = "<div style='margin-top:6px'>⏳ Testando...</div>";
  let html = "";
  try {
    const r1 = await fetch(url + "/rest/v1/", { headers: H });
    if (r1.status === 401) {
      out.innerHTML = linha(false, "<b>Chave rejeitada</b> pelo Supabase. Copie de novo a chave <b>Publishable</b> (sb_publishable_...) ou <b>anon public</b> (eyJ...). NÃO use a sb_secret nem a do Firebase.");
      return;
    }
    html += linha(true, "Chave aceita pelo Supabase.");
  } catch (e1) {
    out.innerHTML = linha(false, "<b>Sem contato com o Supabase.</b> Confira a internet e se a URL é do tipo https://....supabase.co (sem espaços).");
    return;
  }
  try {
    const r2 = await fetch(url + "/rest/v1/sgc_store?select=chave&limit=1", { headers: H });
    if (r2.status === 404) {
      html += linha(false, "<b>A tabela ainda não foi criada no Supabase.</b> Rode o arquivo supabase-setup.sql no SQL Editor (ETAPA 3 do guia) e clique em Testar de novo.");
    } else if (r2.status === 200) {
      html += linha(true, "Tabela sgc_store existe e responde.");
      html += "<div style='margin-top:6px'>🎉 <b>Tudo certo!</b> Agora clique em <b>Salvar e conectar</b>.</div>";
    } else {
      const t2 = await r2.text();
      html += linha(false, "Resposta inesperada (" + r2.status + "): " + t2.slice(0, 120));
    }
  } catch (e2) { html += linha(false, "Falha ao consultar a tabela: " + (e2.message || e2)); }
  out.innerHTML = html;
}

/* Chamado automaticamente por saveLS sempre que algo é gravado. */
function cloudAoSalvar(k, v) {
  try {
    if (cloudChavesSincronizadas().indexOf(k) < 0) return;
    const m = cloudMeta();
    m.chaves[k] = m.chaves[k] || {};
    m.chaves[k].sujo = true; /* marca até a nuvem confirmar o recebimento */
    cloudSalvarMeta(m);
    if (!cloudHabilitada()) return;
    clearTimeout(cloudTimers[k]);
    cloudTimers[k] = setTimeout(function () { cloudEnviarChave(k); }, 400);
  } catch (e) { console.warn("Nuvem: erro no hook de salvamento", e); }
}

/* Envia UMA gaveta de dados para a nuvem (agrupa salvamentos em sequência). */
async function cloudEnviarChave(k) {
  const cli = cloudGetClient(); if (!cli) return;
  const raw = localStorage.getItem(k);
  if (raw === null) return;
  let valor; try { valor = JSON.parse(raw); } catch (e) { return; }
  const agora = new Date().toISOString();
  cloudPendentes[k] = true; cloudAtualizarIndicador("enviando");
  try {
    const r = await cli.from(CLOUD_TABELA).upsert(
      { app_id: CLOUD_APP_ID, chave: k, valor: valor, origem: cloudDeviceId(), updated_at: agora },
      { onConflict: "app_id,chave" }
    );
    if (r.error) throw r.error;
    delete cloudPendentes[k];
    const m = cloudMeta(); m.chaves[k] = { ts: agora, sujo: false }; cloudSalvarMeta(m);
    cloudUltimoSync = new Date().toISOString();
    cloudOnline = true; cloudAtualizarIndicador("ok");
  } catch (e) {
    console.warn("Nuvem: erro ao enviar", k, e);
    cloudUltimoErro = cloudTraduzirErro(e); cloudOnline = false; cloudAtualizarIndicador("offline");
    cloudTimers[k] = setTimeout(function () { cloudEnviarChave(k); }, 15000); /* tenta de novo sozinho */
  }
}

/* Envia TODAS as gavetas (usado na 1ª configuração e no menu Nuvem). */
async function cloudEnviarTudo(silencioso) {
  const cli = cloudGetClient();
  if (!cli) { if (!silencioso) alert("Nuvem não configurada. Use: ☁️ Nuvem → Configurar conexão..."); return; }
  if (!silencioso && !confirm("⬆️ Enviar TODOS os dados deste computador para a nuvem?\n\nO conteúdo da nuvem será substituído pelo que está neste computador.")) return;
  const regs = [];
  cloudChavesSincronizadas().forEach(function (k) {
    const raw = localStorage.getItem(k);
    if (raw === null) return;
    try { regs.push({ app_id: CLOUD_APP_ID, chave: k, valor: JSON.parse(raw), origem: cloudDeviceId(), updated_at: new Date().toISOString() }); } catch (e) { }
  });
  if (!regs.length) { if (!silencioso) alert("Nada para enviar."); return; }
  cloudAtualizarIndicador("enviando");
  try {
    const r = await cli.from(CLOUD_TABELA).upsert(regs, { onConflict: "app_id,chave" });
    if (r.error) throw r.error;
    const m = cloudMeta();
    regs.forEach(function (reg) { m.chaves[reg.chave] = { ts: reg.updated_at, sujo: false }; });
    cloudSalvarMeta(m);
    cloudUltimoSync = new Date().toISOString();
    cloudOnline = true; cloudAtualizarIndicador("ok");
    if (!silencioso) alert("✅ Enviado! " + regs.length + " gaveta(s) de dados estão na nuvem.");
    setStatus("☁️ Dados enviados para a nuvem");
  } catch (e) {
    cloudUltimoErro = cloudTraduzirErro(e); cloudOnline = false; cloudAtualizarIndicador("offline");
    console.warn("Nuvem: erro ao enviar tudo", e);
    if (!silencioso) alert("⚠️ Não consegui enviar agora:\n\n" + cloudUltimoErro + "\n\nO sistema segue salvando aqui e tentará de novo sozinho.");
  }
}

/* Baixa TUDO da nuvem, substituindo os dados deste computador. */
async function cloudBaixarTudo() {
  const cli = cloudGetClient();
  if (!cli) { alert("Nuvem não configurada. Use: ☁️ Nuvem → Configurar conexão..."); return; }
  if (!confirm("⬇️ Baixar TODOS os dados da nuvem?\n\n⚠️ Os dados deste computador serão SUBSTITUÍDOS pelos da nuvem.")) return;
  try {
    const r = await cli.from(CLOUD_TABELA).select("chave,valor,updated_at").eq("app_id", CLOUD_APP_ID);
    if (r.error) throw r.error;
    const linhas = r.data || [];
    if (!linhas.length) { alert("A nuvem ainda está vazia para este banco (" + CLOUD_APP_ID + ")."); return; }
    const meta = cloudMeta();
    linhas.forEach(function (l) {
      if (cloudChavesSincronizadas().indexOf(l.chave) >= 0) {
        localStorage.setItem(l.chave, JSON.stringify(l.valor));
        meta.chaves[l.chave] = { ts: l.updated_at, sujo: false };
      }
    });
    cloudSalvarMeta(meta);
    cloudOnline = true; cloudAtualizarIndicador("recebeu");
    carregarStorage();
    atualizarTabelaPombos(); atualizarTabelaConcorrentes(); atualizarTabelaCursos();
    alert("✅ Dados da nuvem aplicados neste computador.");
    setStatus("☁️ Dados baixados da nuvem");
  } catch (e) {
    console.warn("Nuvem: erro ao baixar", e);
    alert("⚠️ Erro ao baixar da nuvem:\n" + (e.message || e));
  }
}

/* Sincronização inicial (antes do sistema abrir as telas). */
async function cloudSincronizarNoBoot() {
  const cli = cloudGetClient(); if (!cli) return;
  try {
    const r = await cli.from(CLOUD_TABELA).select("chave,valor,updated_at,origem").eq("app_id", CLOUD_APP_ID);
    if (r.error) throw r.error;
    const linhas = r.data || [];
    const meta = cloudMeta();
    cloudOnline = true;
    if (!linhas.length) {
      /* Nuvem vazia: se este PC tem dados, eles sobem (é a migração inicial) */
      await cloudEnviarTudo(true);
      cloudAtualizarIndicador("ok");
      return;
    }
    const mapa = {}; linhas.forEach(function (l) { mapa[l.chave] = l; });
    let aplicou = 0;
    cloudChavesSincronizadas().forEach(function (k) {
      const row = mapa[k]; const m = meta.chaves[k];
      if (row) {
        if (!m || !m.sujo || !m.ts) {
          if (!m || !m.ts || cloudTs(row.updated_at) > cloudTs(m.ts)) {
            localStorage.setItem(k, JSON.stringify(row.valor));
            meta.chaves[k] = { ts: row.updated_at, sujo: false };
            aplicou++;
          }
        } else if (m.sujo) {
          /* este PC editou offline: a versão local sobe e prevalece */
          cloudEnviarChave(k);
        }
      } else if (localStorage.getItem(k) !== null) {
        cloudEnviarChave(k); /* gaveta ainda inexistente na nuvem */
      }
    });
    cloudSalvarMeta(meta);
    cloudAtualizarIndicador(aplicou ? "recebeu" : "ok");
  } catch (e) {
    console.warn("Nuvem: sem contato no boot (seguindo com dados locais)", e);
    cloudUltimoErro = cloudTraduzirErro(e); cloudOnline = false; cloudAtualizarIndicador("offline");
  }
}

/* Realtime: aplica no instante o que outros computadores gravarem. */
function cloudAssinarTempoReal() {
  const cli = cloudGetClient(); if (!cli || cloudInscricao) return;
  try {
    cloudInscricao = cli.channel("sgc-live-" + CLOUD_APP_ID)
      .on("postgres_changes", { event: "*", schema: "public", table: CLOUD_TABELA, filter: "app_id=eq." + CLOUD_APP_ID }, function (payload) {
        const row = payload.new;
        if (!row || !row.chave) return;
        if (row.origem === cloudDeviceId()) return; /* eco do próprio PC */
        cloudReceberAtualizacao(row.chave, row.valor, row.updated_at);
      })
      .subscribe(function (st) {
        if (st === "SUBSCRIBED") { cloudTempoRealOk = true; cloudPararPolling(); }
        if (st === "CHANNEL_ERROR" || st === "TIMED_OUT" || st === "CLOSED") { cloudTempoRealOk = false; cloudIniciarPolling(); }
      });
  } catch (e) { console.warn("Nuvem: realtime indisponível", e); }
}

/* Fallback: sem Realtime, busca as novidades a cada 20s (efeito prático igual) */
function cloudIniciarPolling() {
  if (cloudPollingTimer) return;
  cloudPollingTimer = setInterval(cloudChecarNovidades, 20000);
}
function cloudPararPolling() {
  if (cloudPollingTimer) { clearInterval(cloudPollingTimer); cloudPollingTimer = null; }
}
async function cloudChecarNovidades() {
  if (!cloudHabilitada() || !cloudAppIniciado) return;
  if (cloudTempoRealOk) { cloudPararPolling(); return; }
  const cli = cloudGetClient(); if (!cli) return;
  try {
    const r2 = await cli.from(CLOUD_TABELA).select("chave,valor,updated_at,origem").eq("app_id", CLOUD_APP_ID);
    if (r2.error) throw r2.error;
    (r2.data || []).forEach(function (row) {
      if (row.origem !== cloudDeviceId()) cloudReceberAtualizacao(row.chave, row.valor, row.updated_at);
    });
    if (!cloudOnline) { cloudOnline = true; cloudAtualizarIndicador("ok"); }
  } catch (e2) { console.warn("Nuvem: verificação periódica sem contato", e2); }
}

function cloudReceberAtualizacao(k, valor, ts) {
  try {
    if (cloudChavesSincronizadas().indexOf(k) < 0) return;
    const meta = cloudMeta(); const m = meta.chaves[k];
    if (m && m.ts && cloudTs(ts) <= cloudTs(m.ts)) return; /* já temos algo igual ou mais novo */
    if (k === STORE.lancamentos && cloudLancamentoEmEdicao()) {
      cloudRemotoAguardando[k] = { valor: valor, ts: ts }; /* não atrapalha o operador no meio do lançamento */
      cloudMostrarToastNuvem();
      return;
    }
    cloudAplicarRemoto(k, valor, ts);
  } catch (e) { console.warn("Nuvem: erro ao receber atualização", e); }
}

function cloudLancamentoEmEdicao() {
  try {
    if (typeof editandoLancIndex !== "undefined" && editandoLancIndex !== null) return true;
    const w = document.getElementById("winLancamento");
    return !!(w && w.classList.contains("active") && typeof provaAtual !== "undefined" && provaAtual);
  } catch (e) { return false; }
}

function cloudAplicarRemoto(k, valor, ts) {
  localStorage.setItem(k, JSON.stringify(valor));
  const meta = cloudMeta(); meta.chaves[k] = { ts: ts || new Date().toISOString(), sujo: false }; cloudSalvarMeta(meta);
  if (!cloudAppIniciado) return;
  carregarStorage();
  atualizarTabelaPombos(); atualizarTabelaConcorrentes(); atualizarTabelaCursos();
  setStatus("☁️ Dados atualizados de outro computador");
  cloudAtualizarIndicador("recebeu");
}

function cloudMostrarToastNuvem() {
  let t = document.getElementById("cloudToast");
  if (!t) {
    t = document.createElement("div"); t.id = "cloudToast";
    t.onclick = cloudAplicarPendentesRemotos;
    document.body.appendChild(t);
  }
  t.textContent = "☁️ Chegaram lançamentos de outro computador. Termine o lançamento atual e clique aqui para aplicar.";
  t.style.display = "block";
}

function cloudAplicarPendentesRemotos() {
  if (cloudLancamentoEmEdicao()) { alert("Termine (ou feche) o lançamento atual antes de aplicar as atualizações da nuvem."); return; }
  Object.keys(cloudRemotoAguardando).forEach(function (k) {
    const r2 = cloudRemotoAguardando[k];
    localStorage.setItem(k, JSON.stringify(r2.valor));
    const meta = cloudMeta(); meta.chaves[k] = { ts: r2.ts, sujo: false }; cloudSalvarMeta(meta);
  });
  cloudRemotoAguardando = {};
  const t = document.getElementById("cloudToast"); if (t) t.style.display = "none";
  carregarStorage();
  atualizarTabelaPombos(); atualizarTabelaConcorrentes(); atualizarTabelaCursos();
  setStatus("☁️ Atualizações da nuvem aplicadas");
}

/* ----------------------- interface (indicador, modal, menu) -------------- */
function cloudAtualizarIndicador(estado) {
  let el = document.getElementById("cloudStatus");
  if (!el) {
    el = document.createElement("div"); el.id = "cloudStatus";
    el.title = "Sincronização com a nuvem — clique para ver o status";
    el.onclick = cloudMostrarStatus;
    document.body.appendChild(el);
  }
  const cfg = cloudCfg();
  if (!cfg || !cfg.url) { el.textContent = "☁️ modo local"; el.style.color = "#555"; return; }
  if (estado === "enviando" || Object.keys(cloudPendentes).length) { el.textContent = "☁️ ↑ enviando..."; el.style.color = "#805500"; }
  else if (estado === "recebeu") { el.textContent = "☁️ ↓ atualizado"; el.style.color = "#006600"; }
  else if (cloudOnline) { el.textContent = "☁️ online"; el.style.color = "#006600"; }
  else { el.textContent = "☁️ offline — salvando aqui"; el.style.color = "#aa0000"; }
}

function cloudMostrarStatus() {
  const c = cloudCfg();
  const meta = cloudMeta();
  const sujas = Object.keys(meta.chaves).filter(function (k) { return meta.chaves[k] && meta.chaves[k].sujo; });
  alert("☁️ SINCRONIZAÇÃO COM A NUVEM\n\n" +
    "Estado: " + ((c && c.url) ? (cloudOnline ? "conectado" : "configurado, sem contato agora") : "não configurado (modo local)") + "\n" +
    ((c && c.url) ? ("Projeto: " + c.url + "\nBanco: " + (CLOUD_APP_ID === "sgc" ? "Clube (sgc)" : "Regional (reg)") + "\n") : "") +
    "Último envio confirmado: " + (cloudUltimoSync ? new Date(cloudUltimoSync).toLocaleString() : "-") + "\n" +
    "Último erro: " + (cloudUltimoErro || "-") + "\n" +
    "Alterações locais pendentes: " + sujas.length + (sujas.length ? " (" + sujas.join(", ") + ")" : "") + "\n" +
    "ID deste computador: " + cloudDeviceId() + "\n\n" +
    "Configure em: ☁️ Nuvem → Configurar conexão...");
}

function cloudMostrarCarregando(mostrar) {
  let o = document.getElementById("cloudLoading");
  if (!o) {
    o = document.createElement("div"); o.id = "cloudLoading";
    o.innerHTML = '<div style="background:#fff;border:1px solid #888;padding:18px 24px;box-shadow:2px 2px 6px rgba(0,0,0,.3);font-family:Tahoma,Arial;font-size:12px;">☁️ Sincronizando com a nuvem...</div>';
    document.body.appendChild(o);
  }
  o.style.display = mostrar ? "flex" : "none";
}

function cloudAbrirConfig() {
  let ov = document.getElementById("cloudModalOverlay");
  if (!ov) {
    ov = document.createElement("div"); ov.id = "cloudModalOverlay";
    ov.innerHTML =
      '<div class="cloud-modal">' +
      '<div class="cloud-modal-title"><span>☁️ Configurar conexão com a nuvem (Supabase)</span><span style="cursor:pointer" onclick="cloudFecharConfig()">✖</span></div>' +
      '<div class="cloud-modal-body">' +
      '<div style="margin-bottom:8px">Cole os dados do projeto Supabase do clube (painel do Supabase → ⚙️ Project Settings → API).<br>Use a chave <b>Publishable</b> (sb_publishable_...) ou a legada <b>anon public</b> (eyJ...).<br><b style="color:#a00">NUNCA</b> use a chave sb_secret_... — ela é o acesso mestre do banco.<br>Passo a passo completo no arquivo <b>README-NUVEM.md</b>.</div>' +
      '<div id="cloudTesteResultado" style="border-top:1px solid #bbb;margin-top:8px;padding-top:4px;color:#222"></div>' +
      '<b>Project URL</b><br><input id="cloudCfgUrl" placeholder="https://abcd1234.supabase.co">' +
      '<b>Chave pública (Publishable ou anon public)</b><br><input id="cloudCfgKey" placeholder="sb_publishable_... ou eyJhbGci...">' +
      '<div style="color:#555">• No 1º computador configurado, os dados locais <b>sobem</b> para a nuvem.<br>• Nos demais computadores, os dados da nuvem <b>descem</b> sozinhos.<br>• Nada é enviado para nenhum outro servidor além do Supabase do clube.</div>' +
      '</div>' +
      '<div class="cloud-modal-btns"><button class="classic-btn" style="min-width:110px;height:30px" onclick="cloudTestarConexao()">🔎 Testar conexão</button><button class="classic-btn" style="min-width:120px;height:30px" onclick="cloudSalvarConfigDoModal()">💾 Salvar e conectar</button><button class="classic-btn" style="height:30px" onclick="cloudFecharConfig()">Cancelar</button></div>' +
      '</div>';
    document.body.appendChild(ov);
  }
  const c = cloudCfg() || {};
  document.getElementById("cloudCfgUrl").value = c.url || "";
  document.getElementById("cloudCfgKey").value = c.key || "";
  ov.style.display = "flex";
}
function cloudFecharConfig() { const ov = document.getElementById("cloudModalOverlay"); if (ov) ov.style.display = "none"; }

async function cloudSalvarConfigDoModal() {
  const url = cloudNormalizarUrl(document.getElementById("cloudCfgUrl").value);
  const key = document.getElementById("cloudCfgKey").value.trim();
  if (key.indexOf("sb_secret") === 0) { alert("⚠️ ESSA É A CHAVE SECRETA (sb_secret_...).\nEla dá acesso TOTAL ao banco e não pode ficar no sistema.\n\nUse a chave \"Publishable\" (sb_publishable_...) ou a \"anon public\" (eyJ...), que ficam na mesma tela."); return; }
  if (!/^https:\/\/.+/.test(url) || key.length < 20) { alert("Confira os dados:\n• URL começa com https://\n• A chave é bem longa (sb_publishable_... ou eyJ...)"); return; }
  cloudSalvarCfg({ url: url, key: key, avisado: true });
  cloudClient = null; cloudInscricao = null;
  cloudFecharConfig();
  cloudAtualizarIndicador("enviando");
  await cloudSincronizarNoBoot();
  cloudAssinarTempoReal();
  cloudUltimoSync = new Date().toISOString();
  cloudAtualizarIndicador();
  alert(cloudOnline
    ? "✅ Conectado! Os dados foram sincronizados com a nuvem.\n\nA partir de agora tudo é salvo na nuvem automaticamente."
    : "⚠️ Configuração salva, mas não consegui contatar a nuvem agora.\nO sistema segue no modo local e tentará de novo sozinho.\n\nMotivo: " + (cloudUltimoErro || "desconhecido"));
}

function cloudDesconectar() {
  if (!confirm("Desconectar DESTE computador da nuvem?\n\nOs dados continuam salvos aqui (modo local).\nA nuvem do clube NÃO é apagada.")) return;
  cloudPararPolling(); cloudTempoRealOk = false;
  try { if (cloudClient && cloudInscricao) cloudClient.removeChannel(cloudInscricao); } catch (e) { }
  cloudInscricao = null; cloudClient = null; cloudOnline = false;
  localStorage.removeItem(CLOUD_CFG_KEY);
  cloudAtualizarIndicador();
  setStatus("Nuvem desconectada — modo local");
}

function cloudOferecerConfigInicial() {
  const cfg = cloudCfg();
  if (cfg && (cfg.url || cfg.avisado)) return;
  cloudSalvarCfg({ avisado: true, url: "", key: "" });
  setTimeout(function () {
    if (confirm("☁️ NOVIDADE: sincronização na nuvem!\n\nAgora os dados do clube podem ficar salvos na nuvem (Supabase),\ncom backup automático e acesso de vários computadores ao mesmo tempo.\n\nDeseja configurar agora? (dá para fazer depois: menu ☁️ Nuvem → Configurar conexão)")) cloudAbrirConfig();
  }, 600);
}

/* Ponto de entrada: roda ANTES do sistema montar as telas.
   Retorna uma Promise que resolve quando a sincronização inicial terminar. */
function cloudIniciar(callback) {
  cloudMostrarCarregando(true);
  const fim = function () {
    cloudMostrarCarregando(false);
    callback();
    cloudAppIniciado = true;
    cloudAtualizarIndicador();
    cloudAssinarTempoReal();
    cloudIniciarPolling();
    cloudOferecerConfigInicial();
  };
  if (!cloudHabilitada()) { fim(); return Promise.resolve(); }
  let feito = false;
  const finaliza = function () { if (!feito) { feito = true; clearTimeout(guarda); fim(); } };
  const guarda = setTimeout(function () { console.warn("Nuvem: tempo esgotado no boot"); finaliza(); }, 8000);
  return cloudSincronizarNoBoot()
    .then(finaliza)
    .catch(finaliza);
}
"""

# ---------------------------------------------------------------------------
# Substituições comuns (iguais nos dois arquivos)
# ---------------------------------------------------------------------------
def comuns(eol):
    css = CLOUD_CSS.replace("\r\n", eol)
    js = CLOUD_JS.strip().replace("\n", eol).replace("\r\n", eol) if eol == "\r\n" else CLOUD_JS.strip()
    return [
        # 1) CSS da nuvem + CDN do supabase-js logo após o </style> principal
        (
            "</style>" + eol,
            css + "</style>" + eol +
            '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>' + eol,
            1,
        ),
        # 2) Item "☁️ Nuvem" na barra de menus (depois do Backup)
        (
            '    <div class="menu-title menu-backup" onclick="toggleMenu(event,\'backup\')">💾 Backup</div>' + eol,
            '    <div class="menu-title menu-backup" onclick="toggleMenu(event,\'backup\')">💾 Backup</div>' + eol +
            '    <div class="menu-title" style="color:#1e6b1e;font-weight:bold;" onclick="toggleMenu(event,\'nuvem\')">☁️ Nuvem</div>' + eol,
            1,
        ),
        # 3) saveLS ganha o gancho da nuvem
        (
            "function saveLS(k,v){localStorage.setItem(k,JSON.stringify(v))}" + eol,
            "function saveLS(k,v){localStorage.setItem(k,JSON.stringify(v));cloudAoSalvar(k,v)}" + eol,
            1,
        ),
        # 4) Módulo da nuvem completo, logo após loadLS
        (
            'function loadLS(k,fb){try{const d=localStorage.getItem(k);return d?JSON.parse(d):fb}catch(e){return fb}}' + eol,
            'function loadLS(k,fb){try{const d=localStorage.getItem(k);return d?JSON.parse(d):fb}catch(e){return fb}}' + eol +
            js + eol,
            1,
        ),
        # 5) Menu Nuvem no menuData (antes de "sistema:")
        (
            eol + "  sistema:[",
            eol +
            '  nuvem:[{t:"🔧 Configurar conexão...",action:cloudAbrirConfig},{t:"📶 Status da sincronização",action:cloudMostrarStatus},"sep",{t:"⬆️ Enviar tudo para a nuvem agora",action:()=>cloudEnviarTudo(false)},{t:"⬇️ Baixar tudo da nuvem agora",action:cloudBaixarTudo},"sep",{t:"🔌 Desconectar este computador",action:cloudDesconectar}],' + eol +
            "  sistema:[",
            1,
        ),
        # 6) Boot: sincroniza com a nuvem ANTES de montar as telas
        (
            'window.addEventListener("load",function(){' + eol + "  carregarStorage();" + eol,
            "function iniciarAplicativo(){" + eol + "  carregarStorage();" + eol,
            1,
        ),
        (
            "  initPMRFromUrl();" + eol + "  verificarLembreteBackup();" + eol + "});" + eol,
            "  initPMRFromUrl();" + eol + "  verificarLembreteBackup();" + eol + "}" + eol +
            'window.addEventListener("load",function(){cloudIniciar(iniciarAplicativo)});' + eol,
            1,
        ),
        # 7) Versão v2.1 → v2.2 (barra de status inicial)
        (
            "S.G.C-S.P v2.1 | Importa GPC | Pombo Ás | Distância nos relatórios | PM Remote Clock Ativado",
            "S.G.C-S.P v2.2 | Importa GPC | Pombo Ás | Distância nos relatórios | PM Remote Clock Ativado",
            1,
        ),
        # 8) FAQ: onde ficam os dados
        (
            '{cat:"Geral",q:"Onde ficam salvos os meus dados?",a:"Tudo fica salvo no armazenamento local (localStorage) deste navegador, neste computador. Não há servidor nem nuvem — por isso o backup regular é essencial."},',
            '{cat:"Geral",q:"Onde ficam salvos os meus dados?",a:"Com a nuvem configurada (menu ☁️ Nuvem), o banco de dados oficial fica no Supabase e é sincronizado entre todos os computadores do clube em tempo real. Este navegador mantém uma cópia local para o sistema funcionar mesmo sem internet. O backup em arquivo (menu 💾 Backup) continua recomendado. Sem a nuvem configurada, tudo fica apenas neste navegador."},',
            1,
        ),
        # 9) FAQ: sistema travou
        (
            '{cat:"Problemas comuns",q:"O sistema travou ou uma tela ficou em branco, o que fazer?",a:"Recarregue a página (F5). Como os dados ficam salvos no localStorage, nada se perde — só a tela precisa recarregar."},',
            '{cat:"Problemas comuns",q:"O sistema travou ou uma tela ficou em branco, o que fazer?",a:"Recarregue a página (F5). Os dados ficam salvos na nuvem e também na cópia local, então nada se perde — só a tela precisa recarregar."},',
            1,
        ),
        # 10) Comentário do lembrete de backup
        (
            "/* Como tudo fica salvo só no localStorage deste navegador, se alguém limpar" + eol +
            "   os dados do navegador ou trocar de computador sem ter feito backup, os" + eol +
            "   dados do clube se perdem de vez. Este bloco cuida de lembrar o usuário" + eol +
            "   periodicamente de exportar um backup, sem travar o uso do sistema. */",
            "/* Mesmo com a sincronização na nuvem, o backup em arquivo continua valendo" + eol +
            "   como uma camada extra de segurança (e funciona também quando a nuvem não" + eol +
            "   está configurada e os dados existem só no localStorage deste navegador)." + eol +
            "   Este bloco lembra o usuário de exportar o backup periodicamente. */",
            1,
        ),
        # 11) Texto do banner de backup (menciona a nuvem)
        (
            '    ?"Já faz "+Math.floor(diasDesde(ultimoBackupISO))+" dia(s) desde o último backup. Seus dados só existem neste navegador!"' + eol +
            '    :"Você ainda não fez nenhum backup dos dados deste clube. Seus dados só existem neste navegador!";',
            '    ?"Já faz "+Math.floor(diasDesde(ultimoBackupISO))+" dia(s) desde o último backup em arquivo. Mesmo com a nuvem, vale guardar um backup em arquivo!"' + eol +
            '    :"Você ainda não fez nenhum backup em arquivo dos dados deste clube. Mesmo com a nuvem, vale guardar um backup em arquivo!";',
            1,
        ),
        # 12) Item "Nuvem" no texto do Sobre (mesmo trecho nos dois arquivos)
        (
            "📏 Distância nos relatórios')",
            "📏 Distância nos relatórios\\n☁️ Nuvem (Supabase)')",
            1,
        ),
    ]


def por_arquivo(nome):
    """Substituições que diferem entre index.html e regional.html."""
    if nome == "index.html":
        rotulo = "PigeonMaster"
    else:
        rotulo = "PigeonMASTER_REGIONAL"
    return [
        (
            f"<title>S.G.C-S.P v2.1 - CLUBE COLUMBÓFILO LIMEIRENSE ({rotulo})</title>",
            f"<title>S.G.C-S.P v2.2 - CLUBE COLUMBÓFILO LIMEIRENSE ({rotulo})</title>",
            1,
        ),
        (
            f'setStatus("Pronto | v2.1 | {rotulo} Remote Clock (.PMR) Ativo");',
            f'setStatus("Pronto | v2.2 | {rotulo} Remote Clock (.PMR) Ativo");',
            1,
        ),
        (
            f'<div id="homeSubClube">S.G.C-S.P v2.1 - {rotulo}</div>',
            f'<div id="homeSubClube">S.G.C-S.P v2.2 - {rotulo}</div>',
            1,
        ),
        (
            f"alert('S.G.C-S.P v2.1\\nCLUBE COLUMBÓFILO LIMEIRENSE",
            f"alert('S.G.C-S.P v2.2\\nCLUBE COLUMBÓFILO LIMEIRENSE",
            1,
        ),
    ]


def aplicar(nome):
    with open(nome, "r", encoding="utf-8", newline="") as f:
        txt = f.read()
    if "SINCRONIZAÇÃO COM A NUVEM" in txt:
        print(f"[{nome}] patch já aplicado — nada a fazer.")
        return False
    # Detecta o estilo de quebra de linha dominante do arquivo (CRLF ou LF)
    eol = "\r\n" if txt.count("\r\n") > (txt.count("\n") - txt.count("\r\n")) else "\n"
    print(f"[{nome}] quebra de linha detectada: {repr(eol)}")
    n_ok = 0
    for old, new, qtd in comuns(eol) + por_arquivo(nome):
        achados = txt.count(old)
        if achados != qtd:
            print(f"[{nome}] ERRO: âncora encontrada {achados}x (esperado {qtd}x): {old[:70]!r}")
            return None
        txt = txt.replace(old, new, qtd)
        n_ok += 1
    with open(nome, "w", encoding="utf-8", newline="") as f:
        f.write(txt)
    print(f"[{nome}] OK — {n_ok} alterações aplicadas.")
    return True


ok = True
for arq in ("index.html", "regional.html"):
    r = aplicar(arq)
    if r is None:
        ok = False
        print(f"[{arq}] ABORTADO — nenhum arquivo foi gravado para este arquivo.")

sys.exit(0 if ok else 1)
