/**
 * Spinner - Indicateur de chargement
 * 
 * FR: Composant loader simple
 */

// TODO (FR): Implémenter spinner animé
// - Animation CSS
// - Message optionnel
// - Overlay optionnel (fond semi-transparent)

export default function Spinner() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
}

