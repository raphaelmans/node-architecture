# Next.js Local Development

Read [Portless integration](portless.md) for shared installation, worktree identities, child environment, workspace orchestration, and peer-origin wiring. This mapping owns Next.js startup and configuration materialization.

Inspect the actual Next.js environment boundary and existing application-origin variable. Reuse it for local callbacks and absolute links. Development startup maps the tool-resolved origin into that same variable before launching Next.js; application code and schemas stay unaware of Portless. Do not add a second public origin variable or configuration abstraction merely for this tool.

If bridging is required, place it in development tooling after the proxy has supplied the child environment. Preserve the original command, arguments, assigned port, signals, and exit behavior. Parent-shell interpolation can happen too early. Use [Next.js environment documentation](https://nextjs.org/docs/app/guides/environment-variables) applicable to the target version to verify precedence and browser materialization; values cannot be assumed to update after the process or artifact has already captured them.

Install dependencies and update package scripts/configuration using current official integration guidance. Preserve an independent direct Next.js command and its correct direct origin. Derive exact script names, flags, files, and environment keys at execution time. Keep workspace startup inside package tasks and retain the existing root orchestrator; verify environment availability where injection actually happens using its current official docs.

Use [Next.js CLI documentation](https://nextjs.org/docs/app/api-reference/cli/next) for detected startup behavior and [development-origin documentation](https://nextjs.org/docs/app/api-reference/config/next-config-js/allowedDevOrigins) only when relevant. Keep origin allowances narrow; retain cookie, CSRF, callback, and trusted-proxy checks. Check authentication-provider callback restrictions when activated; a working local hostname does not prove the provider accepts it.

Apply the foundations verification to a real Next.js consumer: two simultaneous checkout origins, correct application-origin values and callback destinations, page/request/hot-reload behavior, and direct startup. Record anything not exercised. Do not create a sample application in an architecture documentation repository just to claim live integration verification.
