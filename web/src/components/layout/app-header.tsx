import { auth, signOut } from "@/auth";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";

export async function AppHeader() {
  const session = await auth();
  const user = session?.user;

  return (
    <header className="flex h-14 items-center gap-2 border-b px-4">
      <SidebarTrigger />
      <Separator orientation="vertical" className="h-6" />
      <div className="flex-1" />
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">{user?.name}</span>
        <Avatar className="h-8 w-8">
          <AvatarImage src={user?.image ?? undefined} alt={user?.name ?? ""} />
          <AvatarFallback>
            {user?.name?.charAt(0)?.toUpperCase() ?? "?"}
          </AvatarFallback>
        </Avatar>
        <form
          action={async () => {
            "use server";
            await signOut({ redirectTo: "/" });
          }}
        >
          <Button variant="ghost" size="sm" type="submit">
            Sign Out
          </Button>
        </form>
      </div>
    </header>
  );
}
