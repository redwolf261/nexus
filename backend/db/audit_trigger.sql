-- Audit Log Immutability Trigger
-- Ensures that the audit_logs table is strictly append-only.

CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable. UPDATE and DELETE operations are strictly prohibited.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_log_immutability_trigger ON audit_logs;

CREATE TRIGGER audit_log_immutability_trigger
BEFORE UPDATE OR DELETE OR TRUNCATE ON audit_logs
FOR EACH ROW
EXECUTE FUNCTION prevent_audit_log_modification();
