export function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("sl-SI", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  } catch {
    return "";
  }
}

export function formatDateTime(dateStr: string | undefined): string {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("sl-SI", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export function formatTime(dateStr: string | undefined): string {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    return d.toLocaleTimeString("sl-SI", {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export const FAZA_COLORS: Record<string, string> = {
  RFQ: "#3B82F6",
  Ponudba: "#8B5CF6",
  "Naročilo": "#10B981",
  Tehnologija: "#F59E0B",
  Nabava: "#EF4444",
  Proizvodnja: "#06B6D4",
  Dostava: "#84CC16",
  "Zaključek": "#6B7280",
};

export function getFazaColor(faza: string): string {
  return FAZA_COLORS[faza] || "#6B7280";
}

export function getStatusColor(status: string | undefined): string {
  switch (status) {
    case "Končano": return "#2E7D4F";
    case "Čaka": return "#2C5282";
    case "V obdelavi": return "#B8963E";
    case "Napaka": return "#C53030";
    default: return "#8B95A5";
  }
}

export function getRfqSubcategoryColor(podkat: string | undefined): string {
  switch (podkat) {
    case "Kompletno": return "#2E7D4F";
    case "Nepopolno": return "#B8963E";
    case "Povpraševanje": return "#2C5282";
    case "Repeat Order": return "#7C3AED";
    default: return "#8B95A5";
  }
}

export function getPrioritetaColor(prioriteta: string | undefined): string {
  switch (prioriteta) {
    case "Visoka": return "#C53030";
    case "Srednja": return "#B8963E";
    case "Nizka": return "#2E7D4F";
    default: return "#8B95A5";
  }
}
