import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

export default function AuthErrorPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Access Denied</CardTitle>
          <p className="text-sm text-muted-foreground">
            You are not authorized to access this application.
          </p>
        </CardHeader>
        <CardContent className="flex justify-center">
          <Button asChild variant="outline">
            <Link href="/">Go Home</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
