export interface Email {
  id: number;
  zadeva?: string;
  posiljatelj?: string;
  prejemniki?: string;
  kategorija?: string;
  rfqPodkategorija?: string;
  status?: string;
  datum?: string;
  analizaStatus?: string;
  analizaRezultat?: Record<string, unknown>;
  priloge?: Array<{ name: string; downloaded: boolean }>;
  izvleceniPodatki?: Record<string, unknown>;
}
