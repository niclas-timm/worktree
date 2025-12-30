import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="container-wide flex items-center justify-between h-16">
          <h1 className="text-xl font-semibold">Ticketing</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              {user?.email}
            </span>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="container-wide py-8">
        <Card>
          <CardHeader>
            <CardTitle>Welcome to Dashboard</CardTitle>
            <CardDescription>
              You have successfully logged in.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p>
                <span className="text-muted-foreground">Email:</span>{" "}
                {user?.email}
              </p>
              {user?.name && (
                <p>
                  <span className="text-muted-foreground">Name:</span>{" "}
                  {user?.name}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
