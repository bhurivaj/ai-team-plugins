# Virtual office (Milestone 1)

Pixel-art office: Entra login, WebSocket game server, canvas client. Which floors a person may enter is set in the security room, not in Entra.

## Admin steps

1. **Entra app** (single tenant). Web redirect URI: `PUBLIC_URL/auth/callback`. Create a client secret.
   - Create the security group `AI-Office-Users`, add the users, put its object id in `OFFICE_GROUP_ID`.
   - Manifest: `"groupMembershipClaims": "SecurityGroup"` so the ID token carries `groups`. A user in more than ~200 groups gets no `groups` claim (overage) and is refused login: the app fails closed.
   - Token configuration: add the **optional claim `auth_time`** to the ID token. Without it the security room keeps asking admins to sign in again (the fresh-sign-in check fails closed).
   - `ADMIN_USERS` takes Entra **Object IDs**, not sign-in names: Entra admin center → Users → pick the person → Object ID.
2. **MFA** comes from an Entra Conditional Access policy requiring MFA for this app. The app does not do MFA itself; it only enforces sign-in freshness (10 minutes) for security-room changes.
3. **Cloudflare:** a proxied DNS record for the hostname; SSL mode Full (strict) with a Cloudflare origin certificate on nginx; a Cloudflare Access application in front of the hostname. nginx must pass WebSocket upgrades (see `nginx.conf.example`).
4. **Server:**
   ```
   cd deploy/virtual-office
   cp .env.example .env && chmod 600 .env    # fill in the values
   docker compose up -d --build
   ```
   Install `nginx.conf.example` as the site config and reload nginx.

`PUBLIC_URL` must be exactly the browser-facing origin (scheme + host, no path, e.g. `https://office.example.com`). `/ws` rejects any upgrade whose `Origin` header differs from it.

## Operations

- Health: `curl -s 127.0.0.1:8080/healthz` returns `{"status": "ok"}`.
- Maps and catalog live in `data/` (Tiled-compatible JSON), bind-mounted read-only. Edit, commit, then `docker compose restart office`. Maps are validated at startup; a broken map fails fast with the `ValueError` message in `docker compose logs office`.
- Access grants and the audit log are in the `office-data` volume (`office.db`).

## Milestone 1 proven

Two browsers, two users, against the real Entra app. Not yet run.

- [ ] Both users see each other move.
- [ ] A non-granted user is stopped at the lift.
- [ ] The owner grants access in the security room and the other user can ride at once.
- [ ] The owner revokes access and the other user is back in the lobby with the toast.
- [ ] The audit list shows both changes.
