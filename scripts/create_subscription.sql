\set ON_ERROR_STOP on

-- Проверяем, существует ли подписка
SELECT EXISTS (
  SELECT 1 FROM pg_subscription WHERE subname = 'my_subscription'
) AS sub_exists;
\gset

\echo :sub_exists

\if :sub_exists
  \echo 'Subscription already exists'
\else
  -- Убедимся, что схема public существует
  CREATE SCHEMA IF NOT EXISTS public;

  -- Создаём подписку
  CREATE SUBSCRIPTION my_subscription
    CONNECTION 'host=postgres-master port=5432 user=repl_user password=repl_password dbname=test_db'
    PUBLICATION my_publication;
\endif
