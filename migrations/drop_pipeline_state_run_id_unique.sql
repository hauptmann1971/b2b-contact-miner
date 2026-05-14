-- pipeline_state: allow multiple rows per run_id (StateManager creates one "started" row then per-keyword rows).
-- Safe to run once; fails if index was already recreated as non-unique.
ALTER TABLE pipeline_state DROP INDEX ix_pipeline_state_run_id;
CREATE INDEX ix_pipeline_state_run_id ON pipeline_state (run_id);
