-- 1. Elimina la vecchia versione (necessario per cambiare il tipo di ritorno)
drop function if exists match_interactions;

-- 2. Crea la nuova versione corretta
create or replace function match_interactions (
-- Usiamo 1536 dimensioni (standard per text-embedding-3-small di OpenAI)
alter table interactions 
add column if not exists embedding vector(1536);

-- 3. Crea indice HNSW per ricerca veloce (opzionale ma consigliato per performance)
create index on interactions using hnsw (embedding vector_cosine_ops);

-- 4. Funzione per ricerca semantica (similarity search)
create or replace function match_interactions (
  query_embedding vector(1536),
  match_threshold float,
  match_count int,
  filter_client_id int default null
)
returns table (
  id integer,
  codice_cliente int,
  tipo_interazione text,
  data_interazione date, 
  esito text,
  note text,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    interactions.id,
    interactions.codice_cliente,
    interactions.tipo_interazione::text,  -- CAST esplicito a text
    interactions.data_interazione,
    interactions.esito::text,             -- CAST esplicito a text
    interactions.note::text,              -- CAST esplicito a text
    1 - (interactions.embedding <=> query_embedding) as similarity
  from interactions
  where 1 - (interactions.embedding <=> query_embedding) > match_threshold
  and (filter_client_id is null or interactions.codice_cliente = filter_client_id)
  order by interactions.embedding <=> query_embedding
  limit match_count;
end;
$$;
