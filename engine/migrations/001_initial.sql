-- Reference schema applied by Store, version 1
CREATE TABLE audit (
          seq INTEGER PRIMARY KEY, payload TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL);
CREATE TABLE records (
          seq INTEGER PRIMARY KEY, kind TEXT NOT NULL, id TEXT NOT NULL,
          payload TEXT NOT NULL, UNIQUE(kind,id));
CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'append only'); END;
CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'append only'); END;
CREATE TRIGGER records_no_delete BEFORE DELETE ON records BEGIN SELECT RAISE(ABORT,'append only'); END;
CREATE TRIGGER records_no_update BEFORE UPDATE ON records BEGIN SELECT RAISE(ABORT,'append only'); END;
PRAGMA user_version=1;
