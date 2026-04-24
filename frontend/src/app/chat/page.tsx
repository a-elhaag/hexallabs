import { redirect } from "next/navigation";
import { createClient } from "~/lib/supabase/server";
import { ChatShell } from "~/components/chat/ChatShell";

export default async function ChatPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    redirect("/login?redirect=/chat");
  }
  return <ChatShell userEmail={user.email ?? ""} />;
}
