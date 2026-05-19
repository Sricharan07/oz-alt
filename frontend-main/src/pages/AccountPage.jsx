import { KeyRound, LogIn, Settings, Shield, UserRound } from "lucide-react";
import { runtimeConfig } from "../config.js";
import { ActionCard, Page } from "../components/ui/index.js";

export function AccountPage() {
  const config = runtimeConfig();

  return (
    <Page title="Account" description="Use backend-backed account pages for password, sessions, and device approval.">
      <div className="action-grid">
        <ActionCard title="Sign in" body="Create or resume a web session." href="/sign-in" icon={LogIn} />
        <ActionCard title="Create account" body="Use the public account creation flow." href="/sign-up" icon={UserRound} />
        <ActionCard title="Approve CLI device" body="Enter the device code shown by oz login." href="/device" icon={KeyRound} />
        <ActionCard title="Session settings" body="Change password and revoke CLI sessions." href="/account" icon={Shield} />
        <ActionCard title="Admin" body="Open operator tools for catalog, crawls, and promotions." href={config.adminUrl} icon={Settings} />
      </div>
    </Page>
  );
}
