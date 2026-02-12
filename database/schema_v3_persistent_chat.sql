-- AI Agent v3 - Persistent Chat & Pending Actions
-- Aplicira ChatHistory tabelo (iz schema_v2) in razširi CakajočeAkcije
-- Zaženi po schema_v2_chat_history.sql

-- 1. Dodaj user_id v CakajočeAkcije (kdo je kreiral akcijo)
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'ai_agent' AND TABLE_NAME = 'CakajočeAkcije' AND COLUMN_NAME = 'user_id'
)
BEGIN
    ALTER TABLE ai_agent.CakajočeAkcije ADD user_id INT;
    ALTER TABLE ai_agent.CakajočeAkcije ADD CONSTRAINT FK_CakajočeAkcije_CreatedBy
        FOREIGN KEY (user_id) REFERENCES ai_agent.Uporabniki(id);
    CREATE INDEX IX_CakajočeAkcije_UserId ON ai_agent.CakajočeAkcije(user_id);
    PRINT 'Dodana kolona user_id v CakajočeAkcije';
END
GO

-- 2. Dodaj rezultat kolono v CakajočeAkcije (JSON rezultat izvedbe)
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'ai_agent' AND TABLE_NAME = 'CakajočeAkcije' AND COLUMN_NAME = 'rezultat'
)
BEGIN
    ALTER TABLE ai_agent.CakajočeAkcije ADD rezultat NVARCHAR(MAX);
    PRINT 'Dodana kolona rezultat v CakajočeAkcije';
END
GO

PRINT 'Schema v3 (persistent chat) uspešno aplicirana!';
GO
