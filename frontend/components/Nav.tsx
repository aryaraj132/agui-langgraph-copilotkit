"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/chat", label: "Chat" },
  { href: "/segment", label: "Segment" },
  { href: "/template", label: "Template" },
  { href: "/campaign", label: "Campaign" },
  { href: "/custom-property", label: "Properties" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="border-b border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center justify-between">
      <Link href="/" className="text-lg font-semibold">
        AG-UI Demo
      </Link>
      <nav className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
        {links.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              pathname === href
                ? "bg-white dark:bg-gray-700 shadow-sm"
                : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            }`}
          >
            {label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
