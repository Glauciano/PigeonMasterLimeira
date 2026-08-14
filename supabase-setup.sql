-- ============================================================================
-- PigeonMaster Limeira — Configuração do banco de dados na nuvem (Supabase)
-- ----------------------------------------------------------------------------
-- Como usar:
--   1. Crie um projeto gratuito em https://supabase.com
--   2. No painel do projeto, abra: SQL Editor → New query
--   3. Cole TODO este arquivo e clique em "Run"
--   4. Pronto. A tabela abaixo guarda os dados das DUAS versões do sistema
--      (index.html usa app_id 'sgc' e regional.html usa app_id 'reg'),
--      separadas na mesma tabela, sem se misturar.
-- ============================================================================

-- Tabela única de sincronização: cada linha é uma "gaveta" de dados do sistema
-- (pombos, concorrentes, cursos, lancamentos, classificacoes, param, pmr_links)
create table if not exists public.sgc_store (
  app_id     text        not null,             -- 'sgc' (clube) ou 'reg' (regional)
  chave      text        not null,             -- ex.: 'sgc_pombos', 'sgc_lancamentos'
  valor      jsonb       not null,             -- conteúdo (lista/cadastro completo)
  origem     text,                             -- id do computador que gravou por último
  updated_at timestamptz not null default now(),
  primary key (app_id, chave)
);

-- Necessário para o Realtime enviar atualizações completas
alter table public.sgc_store replica identity full;

-- Segurança: com estas políticas, qualquer pessoa que tenha a URL e a chave
-- "anon" do projeto consegue ler/gravar. Como a chave fica só nos computadores
-- do clube, isso é suficiente para o uso interno. NÃO publique a chave.
alter table public.sgc_store enable row level security;

drop policy if exists sgc_select on public.sgc_store;
drop policy if exists sgc_insert on public.sgc_store;
drop policy if exists sgc_update on public.sgc_store;
drop policy if exists sgc_delete on public.sgc_store;

create policy sgc_select on public.sgc_store for select to anon using (true);
create policy sgc_insert on public.sgc_store for insert to anon with check (true);
create policy sgc_update on public.sgc_store for update to anon using (true) with check (true);
create policy sgc_delete on public.sgc_store for delete to anon using (true);

-- Liga a sincronização em tempo real nesta tabela (vários PCs ao mesmo tempo)
do $$
begin
  alter publication supabase_realtime add table public.sgc_store;
exception
  when duplicate_object then null; -- já estava ligada, tudo certo
end $$;
