-- Run in Supabase SQL editor (or psql) if circuit breaker jobs fail with PGRST204.
ALTER TABLE public.circuit_breakers
  ADD COLUMN IF NOT EXISTS half_open_success_count integer NOT NULL DEFAULT 0;

COMMENT ON COLUMN public.circuit_breakers.half_open_success_count IS
  'Successful probe count while breaker is HALF_OPEN before returning to CLOSED';
