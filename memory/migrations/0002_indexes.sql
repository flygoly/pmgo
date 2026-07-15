-- Indexes for common project-scoped filters (risk scan, lists).
CREATE INDEX IF NOT EXISTS idx_risks_project_status
ON risks(project_id, status);

CREATE INDEX IF NOT EXISTS idx_milestones_project
ON milestones(project_id);

CREATE INDEX IF NOT EXISTS idx_decisions_project
ON decisions(project_id);

CREATE INDEX IF NOT EXISTS idx_retrospectives_project
ON retrospectives(project_id);

INSERT OR IGNORE INTO schema_migrations(version) VALUES ('0002');
