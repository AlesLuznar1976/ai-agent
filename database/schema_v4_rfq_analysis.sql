-- ============================================================
-- Schema V4: RFQ Deep Analysis
-- Dodaj kolone za analizo povpraševanj v Emaili tabelo
-- ============================================================

ALTER TABLE ai_agent.Emaili ADD analiza_status NVARCHAR(50) NULL;     -- NULL/Čaka/V obdelavi/Končano/Napaka
ALTER TABLE ai_agent.Emaili ADD analiza_rezultat NVARCHAR(MAX) NULL;  -- JSON rezultat analize

CREATE INDEX IX_Emaili_AnalizaStatus ON ai_agent.Emaili(analiza_status);
