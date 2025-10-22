/**
 * SideNav - Navigation latérale
 * 
 * FR: Barre de navigation latérale avec logo et pages
 */

"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import Image from "next/image";

const navigation = [
  {
    name: "📊 Upload",
    href: "/",
    description: "Télécharger les fichiers"
  },
  {
    name: "💡 Besoins",
    href: "/needs",
    description: "Sélectionner les besoins"
  },
  {
    name: "🎯 Cas d'usage",
    href: "/usecases",
    description: "Choisir les cas d'usage"
  },
  {
    name: "📄 Résultats",
    href: "/results",
    description: "Télécharger le rapport"
  }
];

export function SideNav() {
  const pathname = usePathname();

  return (
    <div className="fixed left-0 top-0 h-full w-64 bg-white shadow-lg border-r border-gray-200 z-50">
      {/* FR: Logo en haut */}
      <div className="p-6 border-b border-gray-200">
        <Image
          src="/logoAiko.jpeg"
          alt="Aiko Logo"
          width={120}
          height={40}
          className="h-10 w-auto"
        />
        <p className="text-xs text-gray-500 mt-2">
          Analyse de Besoins & Cas d'Usage IA
        </p>
      </div>

      {/* FR: Navigation */}
      <nav className="p-4">
        <ul className="space-y-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={`block px-4 py-3 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-500 font-semibold'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <div className="flex items-center">
                    <span className="text-lg mr-3">{item.name.split(' ')[0]}</span>
                    <div>
                      <div className="font-medium">{item.name.split(' ').slice(1).join(' ')}</div>
                      <div className="text-xs text-gray-500">{item.description}</div>
                    </div>
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* FR: Footer */}
      <div className="absolute bottom-4 left-4 right-4">
        <div className="text-xs text-gray-400 text-center">
          aikoGPT v1.0
        </div>
      </div>
    </div>
  );
}