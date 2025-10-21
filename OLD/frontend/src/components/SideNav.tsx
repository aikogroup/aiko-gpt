"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { useUiStore } from "@/lib/store";

const links = [
  { href: "/", label: "Accueil" },
  { href: "/validation/needs", label: "Validation besoins" },
  { href: "/validation/use-cases", label: "Validation use cases" },
  { href: "/results", label: "Résultats" },
];

export function SideNav() {
  const pathname = usePathname();
  const { isBusy, phase } = useUiStore();
  return (
    <aside className="w-64 shrink-0 bg-white h-screen border-r border-gray-300">
      <div className="p-4 border-b border-gray-300">
        {/* Le fichier doit être placé dans frontend/public/logoAiko.jpeg */}
        <Image src="/logoAiko.jpeg" alt="Logo" width={224} height={64} className="w-full h-auto" />
      </div>
      <nav className="p-4 space-y-1">
        {links.map((l) => {
          const active = pathname === l.href;
          // Règles d'accès:
          // - Accueil toujours accessible
          // - Validation besoins accessible en phase "needs"
          // - Validation use cases accessible en phase "usecases"
          // - Résultats accessible en phase "done"
          const isHome = l.href === "/";
          const allowNeeds = l.href === "/validation/needs" && (phase === "needs");
          const allowUseCases = l.href === "/validation/use-cases" && (phase === "usecases");
          // Résultats toujours accessibles
          const allowResults = l.href === "/results";
          const allowed = isHome || allowNeeds || allowUseCases || allowResults;
          return (
            <Link
              key={l.href}
              href={l.href}
              className={`block rounded-md px-3 py-2 ${active ? "bg-blue-100 text-blue-700" : "hover:bg-gray-100"} ${(isBusy || !allowed) ? "pointer-events-none opacity-60" : ""}`}
            >
              {l.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}


