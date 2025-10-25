"use client";

import { signIn } from "next-auth/react";
import Link from "next/link";

export function SignInButton() {
  return (
    <Link
      href="/auth/signin"
      className="inline-flex justify-center rounded-md border border-transparent bg-teal-500 px-6 py-3 text-base font-medium text-white shadow-sm hover:bg-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:ring-offset-2"
    >
      Sign in with Keycloak
    </Link>
  );
}
