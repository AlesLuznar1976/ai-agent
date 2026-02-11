-- AI Agent v2 - Chat History tabela
-- Zaenkrat še ni v uporabi (pogovori so in-memory)
-- To je priprava za persistentno shranjevanje

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'ai_agent' AND TABLE_NAME = 'ChatHistory')
BEGIN
    CREATE TABLE ai_agent.ChatHistory (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL,
        role NVARCHAR(20) NOT NULL,        -- 'user', 'agent', 'system', 'tool'
        content NVARCHAR(MAX),
        tool_name NVARCHAR(100),           -- Ime orodja (če role='tool')
        tool_result NVARCHAR(MAX),         -- Rezultat orodja (JSON)
        projekt_id INT,
        datum DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_ChatHistory_User FOREIGN KEY (user_id) REFERENCES ai_agent.Uporabniki(id)
    );

    CREATE INDEX IX_ChatHistory_UserId ON ai_agent.ChatHistory(user_id);
    CREATE INDEX IX_ChatHistory_Datum ON ai_agent.ChatHistory(datum);
    CREATE INDEX IX_ChatHistory_ProjektId ON ai_agent.ChatHistory(projekt_id) WHERE projekt_id IS NOT NULL;
END
GO
