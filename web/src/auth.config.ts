import type { NextAuthConfig } from "next-auth";
import Google from "next-auth/providers/google";

const allowedEmail = process.env.ALLOWED_EMAIL;

export default {
  trustHost: true,
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
  ],
  callbacks: {
    signIn({ profile }) {
      if (!allowedEmail) return false;
      return profile?.email === allowedEmail;
    },
    authorized({ auth, request }) {
      const isApp = request.headers
        .get("host")
        ?.startsWith("app.");
      if (!isApp) return true;
      return !!auth?.user;
    },
  },
  pages: {
    signIn: "/auth/signin",
    error: "/auth/error",
  },
} satisfies NextAuthConfig;
