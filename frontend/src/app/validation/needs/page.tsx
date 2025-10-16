"use client";
import { useEffect, useState } from "react";
import { getThreadState, sendNeedsValidation } from "@/lib/api-client";
import { Spinner } from "@/components/Spinner";
import { useRouter } from "next/navigation";

export default function NeedsValidationPage() {
  const router = useRouter();
  const [needs, setNeeds] = useState<any[]>([]);
  const [selected, setSelected] = useState<Record<number, boolean>>({});
  const [persistedSelected, setPersistedSelected] = useState<any[]>([]);
  const [comment, setComment] = useState("");
  const [statusMsg, setStatusMsg] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const state = await getThreadState();
        const identified = state?.values?.identified_needs || [];
        setNeeds(identified);
      } catch {}
    })();
  }, []);

  const toggle = (idx: number) => setSelected((s) => ({ ...s, [idx]: !s[idx] }));

  const submit = async () => {
    setSubmitting(true);
    const validated = needs.filter((_, i) => selected[i]);
    const rejected = needs.filter((_, i) => !selected[i]);
    // Mettre à jour l’affichage en haut: on cumule les validés
    setPersistedSelected((prev) => {
      // éviter doublons par theme
      const byTheme = new Set(prev.map((n) => n.theme));
      const unique = validated.filter((n) => !byTheme.has(n.theme));
      return [...prev, ...unique];
    });
    const res = await sendNeedsValidation({
      validated_needs: validated,
      rejected_needs: rejected,
      user_feedback: comment,
    });
    if (!res.ok) {
      setStatusMsg("Erreur validation besoins");
      setSubmitting(false);
      return;
    }
    setStatusMsg("Validation envoyée.");
    // Recharger l’état pour récupérer d’éventuelles nouvelles propositions
    try {
      const state = await getThreadState();
      const identified = state?.values?.identified_needs || [];
      const validatedCount = (state?.values?.validated_needs || []).length;
      setNeeds(identified);
      setSelected({});
      setComment("");
      if (validatedCount >= 5) {
        // Passage automatique à la validation des use cases
        setStatusMsg("Validation terminée. Redirection vers les cas d'usage...");
        setTimeout(() => router.push("/validation/use-cases"), 1000);
        return;
      }
    } catch {}
    setSubmitting(false);
  };

  return (
    <main className="mx-auto max-w-4xl p-6 space-y-6 text-black">
      <h1 className="text-2xl font-semibold">Validation des besoins</h1>
      {/* Bloc des besoins déjà sélectionnés en haut, avec option de désélection */}
      {persistedSelected.length > 0 && (
        <section className="space-y-2">
          <h2 className="text-lg font-medium">Besoins sélectionnés</h2>
          <ul className="space-y-2">
            {persistedSelected.map((n, i) => (
              <li key={i} className="border rounded-md p-3 flex items-start gap-3">
                <button
                  onClick={() =>
                    setPersistedSelected((prev) => prev.filter((_, idx) => idx !== i))
                  }
                  className="text-blue-700 underline text-sm"
                >
                  Désélectionner
                </button>
                <div>
                  <div className="font-medium">{n.theme || "Thème"}</div>
                  {Array.isArray(n.quotes) && n.quotes.length > 0 && (
                    <ul className="list-disc pl-6 text-sm">
                      {n.quotes.map((q: string, qi: number) => <li key={qi}>{q}</li>)}
                    </ul>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
      {needs.length === 0 ? (
        <p>Aucun besoin pour le moment. Revenez plus tard.</p>
      ) : (
        <div className="space-y-4">
          {needs.map((n, i) => (
            <div key={i} className="border rounded-md p-4">
              <div className="flex items-center gap-3">
                <input type="checkbox" checked={!!selected[i]} onChange={() => toggle(i)} />
                <h2 className="font-medium">{n.theme || "Thème"}</h2>
              </div>
              {Array.isArray(n.quotes) && n.quotes.length > 0 && (
                <ul className="list-disc pl-6 mt-2">
                  {n.quotes.map((q: string, qi: number) => (
                    <li key={qi} className="text-sm">{q}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="space-y-2">
        <h3 className="font-medium">Commentaires (optionnel)</h3>
        <textarea value={comment} onChange={(e) => setComment(e.target.value)} className="w-full border rounded-md p-2" rows={4} />
      </div>

      <button disabled={submitting} onClick={submit} className="rounded-md px-4 py-2 text-white disabled:opacity-50" style={{ backgroundColor: submitting ? 'rgb(161, 109, 246)' : '#670ffc' }}>
        {submitting ? (<span className="inline-flex items-center gap-2"><Spinner /> Traitement...</span>) : "Valider la sélection"}
      </button>
      {statusMsg && <p className="text-sm mt-2">{statusMsg}</p>}
    </main>
  );
}


