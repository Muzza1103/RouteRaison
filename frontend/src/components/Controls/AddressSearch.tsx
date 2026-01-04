import { useState } from "react";
import type { LatLon } from "../../types/routeraison";

type NominatimItem = {
  display_name: string;
  lat: string;
  lon: string;
};

export function AddressSearch(props: {
  label: string;
  placeholder?: string;
  onSelect: (p: LatLon) => void;
}) {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<NominatimItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    const query = q.trim();
    if (!query) return;

    setLoading(true);
    setError(null);
    setResults([]);

    try {
      const url = new URL("https://nominatim.openstreetmap.org/search");
      url.searchParams.set("format", "json");
      url.searchParams.set("q", query);
      url.searchParams.set("limit", "5");

      const res = await fetch(url.toString(), {
        headers: {
          "Accept": "application/json",
        },
      });
      if (!res.ok) throw new Error(`Nominatim HTTP ${res.status}`);
      const data = (await res.json()) as NominatimItem[];
      setResults(data);
    } catch (e: any) {
      setError(e?.message ?? "Erreur de géocodage");
    } finally {
      setLoading(false);
    }
  }

  function pick(item: NominatimItem) {
    props.onSelect({ lat: parseFloat(item.lat), lon: parseFloat(item.lon) });
    setResults([]);
  }

  return (
    <div className="addr">
      <div className="label">{props.label}</div>
      <div className="row">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={props.placeholder ?? "Tape une adresse…"}
          onKeyDown={(e) => {
            if (e.key === "Enter") search();
          }}
        />
        <button onClick={search} disabled={loading}>
          {loading ? "…" : "Chercher"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {results.length > 0 && (
        <div className="results">
          {results.map((r, idx) => (
            <button key={idx} className="result" onClick={() => pick(r)}>
              {r.display_name}
            </button>
          ))}
        </div>
      )}

      <div className="hint">
        Astuce : tu peux aussi cliquer sur la carte pour placer les points.
      </div>
    </div>
  );
}