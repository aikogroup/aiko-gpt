"use client";
import React from "react";

type Props = {
  accept: string;
  multiple?: boolean;
  onFiles: (files: File[]) => void;
};

export function UploadZone({ accept, multiple, onFiles }: Props) {
  return (
    <input
      type="file"
      accept={accept}
      multiple={!!multiple}
      onChange={(e) => {
        const files = e.target.files ? Array.from(e.target.files) : [];
        onFiles(files);
      }}
      className="block w-full text-sm text-gray-900 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gray-100 hover:file:bg-gray-200"
    />
  );
}


