import { ImageRun } from 'docx';

// Fonction pour créer un logo (placeholder pour l'instant)
export function createLogo(): ImageRun {
  // Pour l'instant, on utilise un texte stylisé comme logo
  // TODO: Ajouter une vraie image de logo
  return new ImageRun({
    data: new Uint8Array(0), // Placeholder
    transformation: {
      width: 200,
      height: 50,
    },
  });
}
