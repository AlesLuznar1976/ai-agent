-- V5: RFQ Pod-kategorizacija
-- Dodaj stolpec rfq_podkategorija za razlikovanje tipov RFQ emailov
-- Vrednosti: Kompletno, Nepopolno, Povpraševanje, Repeat Order
-- NULL = ni določeno (non-RFQ emaili ali stari emaili)

ALTER TABLE ai_agent.Emaili ADD rfq_podkategorija NVARCHAR(50) NULL;

CREATE INDEX IX_Emaili_RfqPodkategorija ON ai_agent.Emaili(rfq_podkategorija);
