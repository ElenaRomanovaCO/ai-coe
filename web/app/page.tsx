import { redirect } from "next/navigation";

export default function Home() {
  // Middleware bounces unauthenticated users to /login from here.
  redirect("/dashboard");
}
