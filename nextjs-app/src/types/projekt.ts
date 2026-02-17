export interface Projekt {
  id: number;
  stevilkaProjekta: string;
  naziv: string;
  strankaId?: number;
  faza: string;
  status: string;
  datumRfq: string;
  datumZakljucka?: string;
  opombe?: string;
}

export interface ProjektCasovnica {
  id: number;
  projektId: number;
  dogodek: string;
  opis: string;
  staraVrednost?: string;
  novaVrednost?: string;
  datum: string;
  uporabnikAliAgent: string;
}
