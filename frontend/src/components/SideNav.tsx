"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";

const links = [
  { href: "/", label: "Accueil" },
  { href: "/validation/needs", label: "Validation besoins" },
  { href: "/validation/use-cases", label: "Validation use cases" },
  { href: "/results", label: "Résultats" },
];

export function SideNav() {
  const pathname = usePathname();
  return (
    <aside className="w-64 shrink-0 border-r bg-white">
      <div className="p-4 border-b border-gray-300">
        {/* Le fichier doit être placé dans frontend/public/logoAiko.jpeg */}
        <Image src="/logoAiko.jpeg" alt="Logo" width={224} height={64} className="w-full h-auto" />
      </div>
      <nav className="p-4 space-y-1">
        {links.map((l) => {
          const active = pathname === l.href;
          return (
            <Link
              key={l.href}
              href={l.href}
              className={`block rounded-md px-3 py-2 ${active ? "bg-blue-100 text-blue-700" : "hover:bg-gray-100"}`}
            >
              {l.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}


