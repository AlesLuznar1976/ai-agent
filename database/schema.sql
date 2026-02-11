-- AI Agent sistem - SQL Server shema
-- Zaženi kot admin na SQL Server

-- 1. Ustvari shemo
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'ai_agent')
BEGIN
    EXEC('CREATE SCHEMA ai_agent');
END
GO

-- 2. Uporabniki
CREATE TABLE ai_agent.Uporabniki (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(50) UNIQUE NOT NULL,
    password_hash NVARCHAR(255) NOT NULL,
    email NVARCHAR(100),
    ime NVARCHAR(100),
    priimek NVARCHAR(100),
    vloga NVARCHAR(50) NOT NULL DEFAULT 'readonly',
    aktiven BIT DEFAULT 1,
    datum_ustvarjen DATETIME DEFAULT GETDATE(),
    zadnja_prijava DATETIME,
    push_token NVARCHAR(255)
);
GO

-- 3. Projekti
CREATE TABLE ai_agent.Projekti (
    id INT IDENTITY(1,1) PRIMARY KEY,
    stevilka_projekta NVARCHAR(50) UNIQUE NOT NULL,
    naziv NVARCHAR(255) NOT NULL,
    stranka_id INT,  -- FK na Largo.Stranke
    faza NVARCHAR(50) NOT NULL DEFAULT 'RFQ',
    status NVARCHAR(50) NOT NULL DEFAULT 'Aktiven',
    datum_rfq DATETIME NOT NULL DEFAULT GETDATE(),
    datum_zakljucka DATETIME,
    odgovorni_prodaja INT,  -- FK na Uporabniki
    odgovorni_tehnolog INT,  -- FK na Uporabniki
    opombe NVARCHAR(MAX),

    CONSTRAINT FK_Projekti_Prodaja FOREIGN KEY (odgovorni_prodaja)
        REFERENCES ai_agent.Uporabniki(id),
    CONSTRAINT FK_Projekti_Tehnolog FOREIGN KEY (odgovorni_tehnolog)
        REFERENCES ai_agent.Uporabniki(id)
);
GO

CREATE INDEX IX_Projekti_Stevilka ON ai_agent.Projekti(stevilka_projekta);
CREATE INDEX IX_Projekti_Faza ON ai_agent.Projekti(faza);
CREATE INDEX IX_Projekti_Status ON ai_agent.Projekti(status);
CREATE INDEX IX_Projekti_Stranka ON ai_agent.Projekti(stranka_id);
GO

-- 4. Dokumenti
CREATE TABLE ai_agent.Dokumenti (
    id INT IDENTITY(1,1) PRIMARY KEY,
    projekt_id INT NOT NULL,
    tip NVARCHAR(50) NOT NULL DEFAULT 'Drugo',
    naziv_datoteke NVARCHAR(255) NOT NULL,
    verzija INT NOT NULL DEFAULT 1,
    pot_do_datoteke NVARCHAR(500) NOT NULL,
    datum_nalozeno DATETIME DEFAULT GETDATE(),
    nalozil_uporabnik INT,

    CONSTRAINT FK_Dokumenti_Projekt FOREIGN KEY (projekt_id)
        REFERENCES ai_agent.Projekti(id) ON DELETE CASCADE,
    CONSTRAINT FK_Dokumenti_Uporabnik FOREIGN KEY (nalozil_uporabnik)
        REFERENCES ai_agent.Uporabniki(id)
);
GO

CREATE INDEX IX_Dokumenti_Projekt ON ai_agent.Dokumenti(projekt_id);
CREATE INDEX IX_Dokumenti_Tip ON ai_agent.Dokumenti(tip);
GO

-- 5. Emaili
CREATE TABLE ai_agent.Emaili (
    id INT IDENTITY(1,1) PRIMARY KEY,
    outlook_id NVARCHAR(255) UNIQUE NOT NULL,
    projekt_id INT,
    zadeva NVARCHAR(500) NOT NULL,
    posiljatelj NVARCHAR(255) NOT NULL,
    prejemniki NVARCHAR(MAX),
    telo NVARCHAR(MAX),
    kategorija NVARCHAR(50) NOT NULL DEFAULT 'Splošno',
    status NVARCHAR(50) NOT NULL DEFAULT 'Nov',
    datum DATETIME NOT NULL,
    izvleceni_podatki NVARCHAR(MAX),  -- JSON
    priloge NVARCHAR(MAX),  -- JSON array

    CONSTRAINT FK_Emaili_Projekt FOREIGN KEY (projekt_id)
        REFERENCES ai_agent.Projekti(id)
);
GO

CREATE INDEX IX_Emaili_Projekt ON ai_agent.Emaili(projekt_id);
CREATE INDEX IX_Emaili_Kategorija ON ai_agent.Emaili(kategorija);
CREATE INDEX IX_Emaili_Status ON ai_agent.Emaili(status);
CREATE INDEX IX_Emaili_Datum ON ai_agent.Emaili(datum);
GO

-- 6. Čakajoče akcije (human-in-the-loop)
CREATE TABLE ai_agent.CakajočeAkcije (
    id INT IDENTITY(1,1) PRIMARY KEY,
    projekt_id INT,
    tip_akcije NVARCHAR(100) NOT NULL,
    opis NVARCHAR(500) NOT NULL,
    predlagani_podatki NVARCHAR(MAX),  -- JSON
    status NVARCHAR(50) NOT NULL DEFAULT 'Čaka',
    ustvaril_agent NVARCHAR(100),
    datum_ustvarjeno DATETIME DEFAULT GETDATE(),
    potrdil_uporabnik INT,
    datum_potrjeno DATETIME,

    CONSTRAINT FK_CakajočeAkcije_Projekt FOREIGN KEY (projekt_id)
        REFERENCES ai_agent.Projekti(id),
    CONSTRAINT FK_CakajočeAkcije_Uporabnik FOREIGN KEY (potrdil_uporabnik)
        REFERENCES ai_agent.Uporabniki(id)
);
GO

CREATE INDEX IX_CakajočeAkcije_Status ON ai_agent.CakajočeAkcije(status);
GO

-- 7. Delovni nalogi (povezava z Largo)
CREATE TABLE ai_agent.DelovniNalogi (
    id INT IDENTITY(1,1) PRIMARY KEY,
    projekt_id INT NOT NULL,
    largo_dn_id INT,  -- FK na Largo.DelovniNalogi
    stevilka_dn NVARCHAR(50),
    artikel_id INT,
    kolicina DECIMAL(18,4),
    status NVARCHAR(50),
    datum_plan_zacetek DATETIME,
    datum_plan_konec DATETIME,
    datum_dejanski_zacetek DATETIME,
    datum_dejanski_konec DATETIME,
    zadnja_sinhronizacija DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_DelovniNalogi_Projekt FOREIGN KEY (projekt_id)
        REFERENCES ai_agent.Projekti(id)
);
GO

CREATE INDEX IX_DelovniNalogi_Projekt ON ai_agent.DelovniNalogi(projekt_id);
CREATE INDEX IX_DelovniNalogi_LargoDN ON ai_agent.DelovniNalogi(largo_dn_id);
GO

-- 8. CalcuQuote povezava
CREATE TABLE ai_agent.CalcuQuoteRFQ (
    id INT IDENTITY(1,1) PRIMARY KEY,
    projekt_id INT NOT NULL,
    calcuquote_rfq_id NVARCHAR(100),
    status NVARCHAR(50) DEFAULT 'Osnutek',
    datum_vnosa DATETIME DEFAULT GETDATE(),
    bom_verzija INT,
    cena_ponudbe DECIMAL(18,2),
    datum_ponudbe DATETIME,

    CONSTRAINT FK_CalcuQuoteRFQ_Projekt FOREIGN KEY (projekt_id)
        REFERENCES ai_agent.Projekti(id)
);
GO

-- 9. Časovnica projekta
CREATE TABLE ai_agent.ProjektCasovnica (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    projekt_id INT NOT NULL,
    dogodek NVARCHAR(100) NOT NULL,
    opis NVARCHAR(500),
    stara_vrednost NVARCHAR(255),
    nova_vrednost NVARCHAR(255),
    datum DATETIME DEFAULT GETDATE(),
    uporabnik_ali_agent NVARCHAR(100),

    CONSTRAINT FK_Casovnica_Projekt FOREIGN KEY (projekt_id)
        REFERENCES ai_agent.Projekti(id) ON DELETE CASCADE
);
GO

CREATE INDEX IX_Casovnica_Projekt ON ai_agent.ProjektCasovnica(projekt_id);
CREATE INDEX IX_Casovnica_Datum ON ai_agent.ProjektCasovnica(datum);
GO

-- 10. Audit log
CREATE TABLE ai_agent.AuditLog (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id INT,
    action NVARCHAR(50) NOT NULL,
    resource_type NVARCHAR(50),
    resource_id NVARCHAR(50),
    details NVARCHAR(MAX),  -- JSON
    ip_address NVARCHAR(50),
    timestamp DATETIME DEFAULT GETDATE()
);
GO

CREATE INDEX IX_AuditLog_User ON ai_agent.AuditLog(user_id);
CREATE INDEX IX_AuditLog_Timestamp ON ai_agent.AuditLog(timestamp);
CREATE INDEX IX_AuditLog_Action ON ai_agent.AuditLog(action);
GO

-- 11. Aktivne seje
CREATE TABLE ai_agent.AktivneSeje (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    refresh_token_hash NVARCHAR(255),
    naprava NVARCHAR(100),
    ip_address NVARCHAR(50),
    datum_ustvarjen DATETIME DEFAULT GETDATE(),
    datum_poteka DATETIME,

    CONSTRAINT FK_Seje_Uporabnik FOREIGN KEY (user_id)
        REFERENCES ai_agent.Uporabniki(id) ON DELETE CASCADE
);
GO

-- 12. Obvestila
CREATE TABLE ai_agent.Obvestila (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    tip NVARCHAR(50) NOT NULL,
    naslov NVARCHAR(200) NOT NULL,
    sporocilo NVARCHAR(500),
    projekt_id INT,
    prioriteta NVARCHAR(20) DEFAULT 'normal',
    prebrano BIT DEFAULT 0,
    akcija_potrebna BIT DEFAULT 0,
    datum DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_Obvestila_Uporabnik FOREIGN KEY (user_id)
        REFERENCES ai_agent.Uporabniki(id) ON DELETE CASCADE,
    CONSTRAINT FK_Obvestila_Projekt FOREIGN KEY (projekt_id)
        REFERENCES ai_agent.Projekti(id)
);
GO

CREATE INDEX IX_Obvestila_User ON ai_agent.Obvestila(user_id);
CREATE INDEX IX_Obvestila_Prebrano ON ai_agent.Obvestila(prebrano);
GO

-- 13. Vstavi privzetega admin uporabnika
-- Geslo: admin123 (hash z bcrypt)
INSERT INTO ai_agent.Uporabniki (username, password_hash, ime, priimek, vloga, email)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.6FqLAqPiUiPaOe', 'Admin', 'Uporabnik', 'admin', 'admin@luznar.si');
GO

PRINT 'AI Agent shema uspešno ustvarjena!';
GO
