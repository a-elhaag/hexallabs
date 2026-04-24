import { LoginForm } from "./LoginForm";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ redirect?: string }>;
}) {
  const { redirect } = await searchParams;
  return (
    <main
      className="min-h-screen flex items-center justify-center"
      style={{ background: "#2c2c2c" }}
    >
      <LoginForm redirect={redirect} />
    </main>
  );
}
