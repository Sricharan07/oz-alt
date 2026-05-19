import {
  Activity,
  Gauge,
  Library,
  LineChart,
  Terminal,
  UserRound
} from "lucide-react";

export const navItems = [
  { to: "/dashboard", label: "Overview", icon: Activity },
  { to: "/libraries", label: "Libraries", icon: Library },
  { to: "/usage", label: "Usage", icon: LineChart },
  { to: "/setup", label: "Setup", icon: Terminal },
  { to: "/status", label: "Status", icon: Gauge },
  { to: "/settings", label: "Account", icon: UserRound }
];
