import Link from "next/link";

export default function NavLinkItem({
  href,
  label,
  isActive,
}: {
  href: string;
  label: string;
  isActive: boolean;
}) {
  return (
    <Link
      href={href}
      className={isActive ? "of-nav-link of-nav-link-active" : "of-nav-link"}
    >
      {label}
    </Link>
  );
}
