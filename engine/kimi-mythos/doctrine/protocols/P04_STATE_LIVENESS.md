# P04 STATE_LIVENESS — kills U7 (state-blindness)

**TRIGGER:** Before every authed wave AND every ~25 authed requests.

**RULE:** One cheap liveness call (e.g. `GET /api/v4/users/me`). 401 → halt IMMEDIATELY,
mark artifacts "post-token-death", reauth, resume only fresh. Never analyze responses
received after the first 401. Same discipline for IP egress changes, file locks, profile
dirs, docker/socket state: verify before assuming.
