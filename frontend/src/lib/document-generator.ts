import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType, BorderStyle, PageBreak, ImageRun } from 'docx';

export interface Need {
  theme: string;
  quotes: string[];
}

export interface UseCase {
  titre?: string;
  title?: string;
  description?: string;
  ia_utilisee?: string;
}

export interface ReportData {
  companyName: string;
  needs: Need[];
  quickWins: UseCase[];
  structurationIa: UseCase[];
  date: string;
}

export async function generateWordReport(data: ReportData): Promise<Blob> {
  // Charger le logo
  let logoImage: ImageRun | undefined;
  try {
    const logoResponse = await fetch('/logoAiko.jpeg');
    const logoBuffer = await logoResponse.arrayBuffer();
    logoImage = new ImageRun({
      data: new Uint8Array(logoBuffer),
      transformation: {
        width: 200,
        height: 60,
      },
      type: 'png'
    });
  } catch (error) {
    console.warn('Impossible de charger le logo:', error);
  }

  const doc = new Document({
    sections: [{
      properties: {
        page: {
          margin: {
            top: 1440,    // 1 inch
            right: 1440,  // 1 inch
            bottom: 1440, // 1 inch
            left: 1440,   // 1 inch
          },
        },
      },
      children: [
        // En-tête avec logo et titre
        ...(logoImage ? [
          new Paragraph({
            children: [logoImage],
            alignment: AlignmentType.CENTER,
            spacing: { after: 200 }
          })
        ] : [
          new Paragraph({
            children: [
              new TextRun({
                text: "AIKO",
                bold: true,
                size: 48,
                color: "2E86AB"
              })
            ],
            alignment: AlignmentType.CENTER,
            spacing: { after: 200 }
          })
        ]),

        new Paragraph({
          children: [
            new TextRun({
              text: "RAPPORT D'ANALYSE DES BESOINS IA",
              bold: true,
              size: 28,
              color: "2E86AB"
            })
          ],
          alignment: AlignmentType.CENTER,
          spacing: { after: 400 }
        }),

        // Informations de l'entreprise
        new Paragraph({
          children: [
            new TextRun({
              text: `Entreprise: ${data.companyName}`,
              bold: true,
              size: 24
            })
          ],
          spacing: { after: 200 }
        }),

        new Paragraph({
          children: [
            new TextRun({
              text: `Date: ${data.date}`,
              size: 20
            })
          ],
          spacing: { after: 600 }
        }),

        // Section Besoins identifiés
        new Paragraph({
          children: [
            new TextRun({
              text: "1. BESOINS IDENTIFIÉS",
              bold: true,
              size: 28,
              color: "2E86AB"
            })
          ],
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 400, after: 200 }
        }),

        // Tableau des besoins
        ...data.needs.map(need => [
          new Paragraph({
            children: [
              new TextRun({
                text: need.theme,
                bold: true,
                size: 22,
                color: "2E86AB"
              })
            ],
            spacing: { before: 200, after: 100 }
          }),
          ...need.quotes.map(quote => 
            new Paragraph({
              children: [
                new TextRun({
                  text: `• ${quote}`,
                  size: 20,
                  italics: true
                })
              ],
              spacing: { after: 100 },
              indent: { left: 400 }
            })
          )
        ]).flat(),

        // Saut de page
        new Paragraph({
          children: [new PageBreak()],
          spacing: { after: 0 }
        }),

        // Section Cas d'usage IA
        new Paragraph({
          children: [
            new TextRun({
              text: "2. CAS D'USAGE IA PRIORISÉS",
              bold: true,
              size: 28,
              color: "2E86AB"
            })
          ],
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 400, after: 200 }
        }),

        // Sous-section Quick Wins
        new Paragraph({
          children: [
            new TextRun({
              text: "2.1 Quick Wins",
              bold: true,
              size: 24,
              color: "2E86AB"
            })
          ],
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 300, after: 150 }
        }),

        // Tableau des Quick Wins
        ...data.quickWins.map(useCase => [
          new Paragraph({
            children: [
              new TextRun({
                text: useCase.titre || useCase.title || "Cas d'usage",
                bold: true,
                size: 22,
                color: "2E86AB"
              })
            ],
            spacing: { before: 200, after: 100 }
          }),
          ...(useCase.description ? [
            new Paragraph({
              children: [
                new TextRun({
                  text: useCase.description,
                  size: 20
                })
              ],
              spacing: { after: 100 },
              indent: { left: 400 }
            })
          ] : []),
          ...(useCase.ia_utilisee ? [
            new Paragraph({
              children: [
                new TextRun({
                  text: `Technologie IA: ${useCase.ia_utilisee}`,
                  size: 18,
                  color: "666666"
                })
              ],
              spacing: { after: 100 },
              indent: { left: 400 }
            })
          ] : [])
        ]).flat(),

        // Sous-section Structuration IA
        new Paragraph({
          children: [
            new TextRun({
              text: "2.2 Structuration IA",
              bold: true,
              size: 24,
              color: "2E86AB"
            })
          ],
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 300, after: 150 }
        }),

        // Tableau des Structuration IA
        ...data.structurationIa.map(useCase => [
          new Paragraph({
            children: [
              new TextRun({
                text: useCase.titre || useCase.title || "Cas d'usage",
                bold: true,
                size: 22,
                color: "2E86AB"
              })
            ],
            spacing: { before: 200, after: 100 }
          }),
          ...(useCase.description ? [
            new Paragraph({
              children: [
                new TextRun({
                  text: useCase.description,
                  size: 20
                })
              ],
              spacing: { after: 100 },
              indent: { left: 400 }
            })
          ] : []),
          ...(useCase.ia_utilisee ? [
            new Paragraph({
              children: [
                new TextRun({
                  text: `Technologie IA: ${useCase.ia_utilisee}`,
                  size: 18,
                  color: "666666"
                })
              ],
              spacing: { after: 100 },
              indent: { left: 400 }
            })
          ] : [])
        ]).flat(),

        // Pied de page
        new Paragraph({
          children: [
            new TextRun({
              text: "---",
              size: 20,
              color: "CCCCCC"
            })
          ],
          alignment: AlignmentType.CENTER,
          spacing: { before: 400 }
        }),

        new Paragraph({
          children: [
            new TextRun({
              text: "Rapport généré par aikoGPT",
              size: 16,
              color: "999999"
            })
          ],
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 }
        })
      ]
    }]
  });

  const buffer = await Packer.toBuffer(doc);
  return new Blob([new Uint8Array(buffer)], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
}
