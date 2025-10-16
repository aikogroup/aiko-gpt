"use client";
import { useEffect, useState } from "react";
import { getThreadState, sendUseCaseValidation } from "@/lib/api-client";
import { Spinner } from "@/components/Spinner";
import { useRouter } from "next/navigation";

export default function UseCasesValidationPage() {
  const router = useRouter();
  const [quickWins, setQuickWins] = useState<any[]>([]);
  const [structIa, setStructIa] = useState<any[]>([]);
  const [selQw, setSelQw] = useState<Record<number, boolean>>({});
  const [selSia, setSelSia] = useState<Record<number, boolean>>({});
  const [comment, setComment] = useState("");
  const [statusMsg, setStatusMsg] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [persistedSelected, setPersistedSelected] = useState<any[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const state = await getThreadState();
        setQuickWins(state?.values?.proposed_quick_wins || []);
        setStructIa(state?.values?.proposed_structuration_ia || []);
      } catch {}
    })();
  }, []);

  const submit = async () => {
    setSubmitting(true);
    const validated_qw = quickWins.filter((_, i) => selQw[i]);
    const rejected_qw = quickWins.filter((_, i) => !selQw[i]);
    const validated_sia = structIa.filter((_, i) => selSia[i]);
    const rejected_sia = structIa.filter((_, i) => !selSia[i]);

    // Empiler les sélectionnés en haut avec déduplication par titre
    setPersistedSelected((prev) => {
      const byTitle = new Set(prev.map((u) => u.titre || u.title));
      const all = [...validated_qw, ...validated_sia].filter((u) => !(byTitle.has(u.titre || u.title)));
      return [...prev, ...all];
    });

    const res = await sendUseCaseValidation({
      validated_quick_wins: validated_qw,
      validated_structuration_ia: validated_sia,
      rejected_quick_wins: rejected_qw,
      rejected_structuration_ia: rejected_sia,
      user_feedback: comment,
    });
    if (!res.ok) {
      setStatusMsg("Erreur validation use cases");
      setSubmitting(false);
      return;
    }
    setStatusMsg("Validation envoyée.");
    // Charger l'état pour savoir si on a atteint 5 items validés (cumulés)
    try {
      const state = await getThreadState();
      const vqw = state?.values?.validated_quick_wins || [];
      const vsia = state?.values?.validated_structuration_ia || [];
      const total = vqw.length + vsia.length;
      if (total >= 5) {
        router.push("/results");
        return;
      }
      // Sinon, recharger de nouvelles propositions et réinitialiser les sélections
      setQuickWins(state?.values?.proposed_quick_wins || []);
      setStructIa(state?.values?.proposed_structuration_ia || []);
      setSelQw({});
      setSelSia({});
      setComment("");
    } catch {}
    setSubmitting(false);
  };

  return (
    <main className="mx-auto max-w-4xl p-6 space-y-6 text-black">
      <h1 className="text-2xl font-semibold">Validation des cas d'usage</h1>

      {persistedSelected.length > 0 && (
        <section className="space-y-2">
          <h2 className="text-lg font-medium">Sélection en cours (cumulée)</h2>
          <ul className="space-y-2">
            {persistedSelected.map((uc, i) => (
              <li key={i} className="border rounded-md p-3 flex items-start gap-3">
                <button
                  onClick={() => setPersistedSelected((prev) => prev.filter((_, idx) => idx !== i))}
                  className="text-blue-700 underline text-sm"
                >
                  Désélectionner
                </button>
                <div>
                  <div className="font-medium">{uc.titre || uc.title || "Cas d'usage"}</div>
                  {uc.description && <div className="text-sm text-gray-700">{uc.description}</div>}
                  {uc.ia_utilisee && <div className="text-xs text-gray-500">IA: {uc.ia_utilisee}</div>}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="space-y-3">
        <h2 className="font-medium">Quick Wins</h2>
        {quickWins.length === 0 ? (
          <p>Aucun Quick Win</p>
        ) : (
          <div className="space-y-2">
            {quickWins.map((uc, i) => (
              <label key={i} className="flex items-start gap-3 border rounded-md p-3 cursor-pointer">
                <input type="checkbox" checked={!!selQw[i]} onChange={() => setSelQw((s) => ({ ...s, [i]: !s[i] }))} />
                <div>
                  <div className="font-medium">{uc.titre || uc.title || "Cas d'usage"}</div>
                  {uc.description && <div className="text-sm text-gray-700">{uc.description}</div>}
                  {uc.ia_utilisee && <div className="text-xs text-gray-500">IA: {uc.ia_utilisee}</div>}
                </div>
              </label>
            ))}
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="font-medium">Structuration IA</h2>
        {structIa.length === 0 ? (
          <p>Aucune proposition</p>
        ) : (
          <div className="space-y-2">
            {structIa.map((uc, i) => (
              <label key={i} className="flex items-start gap-3 border rounded-md p-3 cursor-pointer">
                <input type="checkbox" checked={!!selSia[i]} onChange={() => setSelSia((s) => ({ ...s, [i]: !s[i] }))} />
                <div>
                  <div className="font-medium">{uc.titre || uc.title || "Cas d'usage"}</div>
                  {uc.description && <div className="text-sm text-gray-700">{uc.description}</div>}
                  {uc.ia_utilisee && <div className="text-xs text-gray-500">IA: {uc.ia_utilisee}</div>}
                </div>
              </label>
            ))}
          </div>
        )}
      </section>

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


