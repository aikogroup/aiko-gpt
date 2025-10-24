import { NextRequest, NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { existsSync } from 'fs';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const files = formData.getAll('files') as File[];
    
    if (files.length === 0) {
      return NextResponse.json({ error: 'No files provided' }, { status: 400 });
    }

    // Créer le dossier uploads s'il n'existe pas
    const uploadDir = join(process.cwd(), 'uploads');
    if (!existsSync(uploadDir)) {
      await mkdir(uploadDir, { recursive: true });
    }

    const uploadedFiles: string[] = [];
    const workshopFiles: string[] = [];
    const transcriptFiles: string[] = [];

    for (const file of files) {
      const bytes = await file.arrayBuffer();
      const buffer = Buffer.from(bytes);
      
      // Générer un nom de fichier unique
      const timestamp = Date.now();
      const fileName = `${timestamp}_${file.name}`;
      const filePath = join(uploadDir, fileName);
      
      // Sauvegarder le fichier
      await writeFile(filePath, buffer);
      uploadedFiles.push(filePath);
      
      // Classifier par type
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        workshopFiles.push(filePath);
      } else if (file.name.endsWith('.pdf')) {
        transcriptFiles.push(filePath);
      }
    }

    return NextResponse.json({
      success: true,
      uploaded_files: uploadedFiles,
      file_types: {
        workshop: workshopFiles,
        transcript: transcriptFiles
      },
      count: uploadedFiles.length
    });

  } catch (error) {
    console.error('Upload error:', error);
    return NextResponse.json(
      { error: 'Upload failed' }, 
      { status: 500 }
    );
  }
}
