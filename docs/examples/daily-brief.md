# Daily Brief: a worked AI feature

Status: proposed application of the architecture playbook, captured 2026-11-14 for review. This is a product example, not a new universal contract or a migration of Ample. Method names in the proposed call trees are illustrative application APIs, not Mastra or AI SDK APIs.

Read with [AI boundaries](../../server/core/ai-boundaries.md), [controllers](../../server/core/controllers.md), [transactions](../../server/core/transaction.md), and [async jobs and outbox](../../server/core/async-jobs-outbox.md). Open the [interactive method call tree](../../assets/daily-brief-call-stack.html).

## Product feature

**Daily Brief gives a professional relevant news and prepared interview opportunities, grounded in their company and target audience.** They can review the brief in their feed and follow an invitation into an interview. Optional email delivery distributes the prepared content; recording interviews and producing clips are downstream features, outside this example.

The client feature is `daily-brief`; the server operations span brief preparation, news ingestion, interview preparation, and delivery. A product feature is not one giant server controller.

Inputs are the authorized recipient, company, target audience, brief date, news lookback, and delivery preference. Current code has a personal variant covering customer, industry, and competitor news, and a target-customer variant covering customer news only. The proposed implementation preserves these variants as explicit application policy.

Outputs are a dated brief with sources, prepared interviews and questions, invitation records, and a visible preparation outcome. Delivery has its own outcome so a failed email does not invalidate a prepared brief.

### Product vocabulary for this example

| Term | Meaning |
| --- | --- |
| Daily brief | A recipient's dated collection of relevant news and interview opportunities |
| Target audience | The customer segment the recipient wants to reach; represented by Ample's customer profile |
| News candidate | A discovered item awaiting validation and a duplicate decision |
| News story | An accepted source-backed news record, reusable by multiple briefs |
| Interview opportunity | A proposed interview for a recipient and target audience, grounded in a news story |
| Brief run | One tracked attempt to prepare the brief, with progress and a result |

These are example-local product terms, not additions to the architecture glossary. In particular, an Ample customer profile is an audience description, not the authenticated recipient or an organization membership.

## What the source actually does

Read-only evidence: local `Work/ample`, clean checkout at `ef4d0338fd6555b7885e9ebfec51adb6e00d8454`. Source root on the inspected machine: `/Users/raphaelm/Documents/Work/ample`. Paths and line numbers below are relative to that checkout. No application, workflow, model call, or email was executed.

| Evidence | Observed behavior |
| --- | --- |
| `src/app/api/daily-brief/trigger/route.ts:40` | HTTP trigger checks internal credentials or a session, accepts a profile id, then starts the personal workflow in background work. The shown route does not establish that the submitted profile belongs to the session user. |
| `src/mastra/workflows/daily-brief.ts:432` | Personal workflow: create daily run → fetch company → summarize context → discover news → generate topics → generate interviews/segments → compose email → persist. |
| `src/mastra/workflows/daily-brief.ts:307` | Target-customer workflow accepts an existing daily run and chosen customer profile, and restricts discovery/persisted news metadata to customer news. |
| `src/mastra/tools/daily-brief/index.ts:171` | News tool obtains services through `servicesBuilder()`. Personal discovery runs three searches concurrently, with a seven-day lookback and limit of three per category. |
| `src/mastra/tools/daily-brief/index.ts:303` | Topic generation uses customer news and audience context. The next tools generate interview segments and consolidated email content. |
| `src/mastra/tools/daily-brief/index.ts:437` | Persistence tool coordinates many services: checks an interview source slug derived from title, customer profile, and recipient; upserts a story; creates interview, match, segment, and invitation records; builds optional email; updates run metadata. |
| `src/lib/extern/services/news-story-service.ts:129` | `upsertByTitle()` writes the story first, then starts background embedding generation. Embedding errors are logged and swallowed. |
| `src/lib/extern/db/supabase/news-story-repo.ts:236` | Story identity conflicts are handled by title using a database upsert. This is not semantic duplicate detection. |
| `src/mastra/workflows/daily-brief.ts:423` and `:545` | Both inspected target-customer and personal variants explicitly set `disableEmail: true`. |
| `src/features/daily-brief-feed/components/daily-brief-feed-content.tsx:23` | Feed reads paginated daily invitation runs, expands the newest result, and handles loading/empty states. Its initial generating indicator is time-based. |

The repo also contains an older `daily-brief-ingestion.ts`; this example follows the `daily-brief.ts` workflow reached by the inspected trigger. It does not claim that every scheduler or production deployment uses that entrypoint.

## Proposed replication under the playbook

Use a workflow because the feature has several external calls, persisted progress, and repeatable stages. Select durable storage and a runner with verified checkpoint/restart behavior; the workflow definition alone does not provide those guarantees. A model does not need to decide the sequence, so an autonomous agent is not required. An optional agent tool may request the same public start operation as the UI.

The composition root creates provider adapters and scoped application factories. Mastra business steps receive narrow controller factories and invoke one framework-neutral controller. The controller delegates to one use case or service. Pure engine mapping or suspension needs no controller. This example uses direct step-to-controller calls; native tool-as-step composition is also allowed when it preserves the same protected controller boundary. Steps never select services through a builder or write business tables.

### 1. Start and return a run id

```text
HTTP adapter OR requestDailyBrief tool
  resolve actor from authenticated context; validate input
  StartDailyBriefController.execute(input, actor)
    StartDailyBriefUseCase.execute(command, actor)
      BriefAccessService.requireCanPrepare(actor, recipient, company, audience)
      transaction
        BriefRunService.createOrGet(requestKey, validatedScope)
        OutboxService.enqueueOnce(startBrief, runId)
      return { runId, status }

AFTER COMMIT — separate execution, not the same JavaScript stack
WorkflowDispatchWorker.handle(startBrief)
  WorkflowRunner.start(runId, persistedScope)        [port → Mastra adapter]
```

The application run id is also the engine run id. Duplicate start delivery attaches to or observes that run rather than creating another one. The request key includes the authorized recipient, date, variant, and selected audience where applicable; an intentional regeneration is a separately identified revision. Date boundaries are explicit product policy, not the worker's local timezone.

Scope records the verified recipient, company, audience selection, and the initiator who requested the brief. Do not infer an organization from a company id; map to organization scope only where the consuming product establishes that tenancy.

Steps have no session. Each step adapter builds `runActor`, the [execution identity](../../server/core/ai-boundaries.md#workflow-steps-call-application-operations): a system principal acting for the recorded initiator. Every business operation reloads the run, checks its allowed transition, and asks `BriefAccessService` whether that initiator may still prepare this brief. Access revoked mid-run ends the run as `accessRevoked`; it does not finish on permission that held only at start. A scheduled brief names the scheduling capability as initiator and is authorized by its scope.

### 2. Resolve context

```text
loadContextStep.execute({ runId, scope })             [Mastra adapter]
  PrepareBriefContextController.execute(input, runActor)
    PrepareBriefContextUseCase.execute(runId, runActor)
      BriefAccessService.requireStillAllowed(runActor, scope)
      BriefContextService.loadAuthorizedInputs(scope)
      CompanySummaryService.summarize(company)
        ModelGateway.generateStructured(prompt, schema, model)
          AiSdkModelAdapter → model provider
      BriefDraftService.saveContext(runId, context)
    return { runId, scope, contextId }
```

Module services own prompts and output schemas. The shared model gateway owns provider calls, validation, usage, and translated provider failures. A rejected generated value becomes an explicit application result; it is not passed downstream as a valid draft.

### 3. Discover, then resolve each candidate

This is the requested search-to-database path, split into two business steps. Discovery runs once. Each candidate then runs as its own step through the engine's iteration with bounded concurrency, so one failed embedding retries one candidate instead of repeating the search and every earlier model call.

```text
discoverNewsStep.execute({ runId, scope })            [Mastra adapter]
  DiscoverBriefNewsController.execute(input, runActor)
    DiscoverBriefNewsUseCase.execute(runId, runActor)   [application]
      BriefAccessService.requireStillAllowed(runActor, scope)
      BriefContextService.load(runId, scope)
      NewsDiscoveryService.search(context, variant)
        NewsSearchPort.search(query)                   [port]
          SearchProviderAdapter → external search
      BriefDraftService.saveCandidates(runId, items)   [raw items + source evidence]
    return { runId, scope, candidateIds }

ENGINE ITERATION — one step per candidateId, bounded concurrency

resolveNewsCandidateStep.execute({ runId, scope, candidateId })
  ResolveNewsCandidateController.execute(input, runActor)
    ResolveNewsCandidateUseCase.execute(candidateId, runActor)
      NewsNormalizationService.normalize(item)
        map known fields; preserve source evidence
        ModelGateway.generateStructured(...)          [only if extraction needs AI]
        validate NewsCandidate                        [application object, not DB row]
      NewsIdentityService.findExact(sourceKey, scope)
        NewsRepository.findBySourceKey(sourceKey, scope)
      if exact existing → reuse storyId; skip embedding
      else
        NewsEmbeddingService.embed(candidate)
          ModelGateway.embed(canonicalText, model)
            AiSdkModelAdapter → embedding provider
        NewsIdentityService.findSimilar(candidate, vector, scope)
          NewsRepository.findSimilar(vector, modelVersion, scope)
          DuplicatePolicy.decide(candidate, matches)
        branch on decision
          same event → link as another source of the existing story; reuse storyId
          new → NewsCatalogService.accept(candidate, vector, scope)
            NewsRepository.insertOrGetBySourceKey(...) [atomic DB operation]
      BriefDraftService.recordDisposition(runId, candidateId, decision, evidence)
    return { candidateId, disposition, storyId }
```

Search adapters may encapsulate provider-owned grounded search. Application-owned normalization, summaries, interview writing, and embeddings use the model gateway. The gateway's structured result is still an application candidate; the repository alone maps it into a database row.

The exact source-key lookup runs before embedding. An exact duplicate costs one indexed read and no model call. The lookup also checks candidates already resolved in this run.

No accepted new story is inserted until its embedding succeeds. Raw candidates saved by discovery are recovery data, not accepted catalog stories. Store embedding model/version and dimensions with the vector and compare only compatible representations. If embedding fails, the candidate's step fails and retries alone; when retries are exhausted, record the candidate as `failed` and let the run continue with the others.

### 4. Generate interview opportunities

```text
prepareInterviewsStep.execute({ runId, scope })
  PrepareBriefInterviewsController.execute(input, runActor)
    PrepareBriefInterviewsUseCase.execute(runId, runActor)
      BriefDraftService.getAcceptedStories(runId, scope)
      InterviewOpportunityService.excludeAlreadyOffered(recipient, audience, storyIds)
      InterviewTopicService.generate(context, eligibleCustomerStories)
        ModelGateway.generateStructured(topicPrompt, topicSchema, model)
      InterviewDraftService.generate(topics)
        ModelGateway.generateStructured(interviewPrompt, interviewSchema, model)
      BriefDraftService.saveInterviews(runId, validatedDrafts)
```

Preserve the current audience/customer-news grounding for interview topics. Industry and competitor news can still appear in the brief. Moving duplicate checks ahead of interview generation avoids paying to generate opportunities that will be discarded. Final persistence must recheck uniqueness because another run can race this one.

### 5. Compose, commit, deliver, and read

```text
composeBriefStep.execute({ runId, scope })
  ComposeDailyBriefController.execute(input, runActor)
    ComposeDailyBriefUseCase.execute(runId, runActor)
      BriefCopyService.compose(acceptedNews, interviewDrafts)
        ModelGateway.generateStructured(prompt, schema, model)
      BriefDraftService.saveCopy(runId, validatedCopy)

publishBriefStep.execute({ runId, scope })
  PublishDailyBriefController.execute(input, runActor)
    PublishDailyBriefUseCase.execute(runId, runActor)
      BriefAccessService.requireStillAllowed(runActor, scope)
      transaction OR one equivalent atomic repository operation
        InterviewOpportunityService.createOnce(recipient, audience, storyId)
        InterviewService.persistDraftsAndInvitations(...)
        DailyBriefService.publish(runId, newsLinks, interviewLinks, copy)
        BriefRunService.markCompleted(runId, result)
        OutboxService.enqueueOnce(briefEmail, runId)    [only if delivery enabled]

AFTER COMMIT — independent delivery worker
DeliverBriefEmailUseCase.execute(deliveryId)
  BriefDeliveryService.loadAndClaim(deliveryId)
  EmailPort.send(content, stableDeliveryKey)
  BriefDeliveryService.recordOutcome(deliveryId)

Client feature → query adapter → featureApi → network
  GetDailyBriefController.execute(input, actor)
    DailyBriefQueryService.getAuthorizedBrief(runId, actor)
      DailyBriefRepository → application records
```

Search, model calls, and email sending occur outside database transactions. The outbox makes delivery recoverable; provider idempotency support and reconciliation determine whether duplicate external sends can be prevented. Do not claim exactly-once email merely because an outbox exists. With delivery disabled, publish the feed without enqueueing email, matching the inspected workflow's preference.

The UI reads application progress/results. It does not inspect Mastra snapshots or infer completion from elapsed time. A failed retryable step records its failure and attempt; retry policies and guarded transitions determine when the run becomes terminally failed. Retrying a completed stage reuses its recorded output.

## Where Zod Fits

Zod is the TypeScript implementation of the playbook's executable data contracts. It already underpins [public API contracts](../../server/core/api-contracts-zod-first.md); the [AI schema ownership rules](../../server/core/ai-boundaries.md#schema-ownership-and-validation) extend that same discipline to model calls and workflow inputs. It is used at boundaries throughout this feature, not inserted as another layer between controllers and services.

The inspected Ample source already defines Zod schemas in `src/mastra/schemas/daily-brief.ts`, including `BriefNewsItemSchema`, interview/topic schemas, and step schemas. Some are composed from database-derived schemas, and application model services import schemas from the Mastra folder. The proposed ownership reverses that dependency: application modules define their contracts independently; Mastra and provider adapters consume them.

| Proposed schema | Owner and placement | Where it runs |
| --- | --- | --- |
| `StartDailyBriefInputSchema`, `StartDailyBriefResponseSchema`, `GetDailyBriefResponseSchema` | Brief module's shared wire contracts | HTTP/tool adapters parse input and response; client parses the network response using the same schema |
| `BriefStepInputSchema` | Brief module's server-only internal contracts | Each workflow entry/resumed step validates serialized `runId` and scope; application logic separately checks access and run state |
| `NewsCandidateSchema` | News module's server-only normalization contracts | Normalization validates mapped search data; when AI extraction is needed, the gateway validates model output against this same schema |
| `InterviewTopicsSchema`, `InterviewDraftSchema`, `BriefCopySchema` | Owning module's server-only generation contracts | Services pass their schema with the prompt; the gateway returns either an accepted typed value or a rejected-output result |
| `EmbeddingResultSchema` | Shared model gateway's application-owned result contract | Adapter validates finite vector values and expected dimensions; the news service checks representation compatibility |
| Persistence row schema, if needed | Repository adapter only | Maps a validated application candidate to storage fields; database constraints still enforce identity and integrity |

These names illustrate ownership; they are not newly implemented schemas. In one project, public brief contracts live under `src/lib/modules/daily-brief/shared/contracts/`; internal generation contracts stay beside the owning module's services or in its server-only schema folder. In a monorepo, activate a shared contract package only when the wire contract crosses package boundaries. Derive types from their schemas rather than writing a second shape by hand.

```text
resolveNewsCandidateStep
  validate internal step input with BriefStepInputSchema
  ResolveNewsCandidateController.execute(input, runActor)
    ResolveNewsCandidateUseCase.execute(typedInput)
      NewsNormalizationService.normalize(rawItem)
        deterministic mapping → NewsCandidateSchema validation
        OR ModelGateway.generateStructured(prompt, NewsCandidateSchema)
          provider output → NewsCandidateSchema validation
          accepted candidate OR rejected-output result
      NewsIdentityService.findExact(...)
        repository lookup on the exact source key
      NewsEmbeddingService.embed(validatedCandidate)
        ModelGateway.embed(...) → validate EmbeddingResult
      NewsIdentityService.findSimilar(candidate, vector, scope)
        application duplicate policy + repository lookup
      NewsCatalogService.accept(candidate, vector, scope)
        repository maps to a row; database enforces exact-key uniqueness
```

A candidate can have a valid title and URL yet describe invented news. A scope id can be well formed yet belong to another user. A vector can have the correct dimensions yet use an incompatible model. Zod guards the value's structure; application rules and trusted evidence decide whether it may proceed. Do not reparse identical trusted values at every internal method call, and do not make a schema refinement perform the database duplicate check.

## Three different duplicate decisions

| Decision | Recommended identity and outcome |
| --- | --- |
| Is this the same source story? | Use a deterministic provider/source identifier or canonical source URL within the authorized catalog scope. Reuse the story. Titles alone are insufficient. |
| Could these sources describe the same event? | Embedding similarity retrieves candidates for `DuplicatePolicy`. A high score alone does not prove identity. Every candidate ends in a terminal disposition; nothing waits in a review queue. |
| Has this recipient already been offered this story for this audience? | Enforce a unique recipient + audience + canonical story relationship. A shared story can legitimately produce opportunities for different recipients. |

Exact-key uniqueness handles concurrent retries of the same source. It does not guarantee semantic uniqueness across different URLs. If strict semantic uniqueness becomes a requirement, add a serialized reconciliation/cluster decision; the initial vector lookup alone cannot provide it. Check candidates within the current batch as well as existing stored stories.

`DuplicatePolicy` ships in two stages, selected by configuration:

1. **Observe (launch default).** Only exact source keys count as duplicates. Similarity still runs and its nearest match and score are recorded on the disposition, but the candidate is accepted as new. This collects the labelled evidence needed to choose a threshold without dropping news on an untested number.
2. **Enforce.** Once a threshold is calibrated against those recorded pairs, a candidate above it that also agrees on deterministic evidence, such as publication window and named company, is linked as another source of the existing story and withheld from the brief as the same event. Below the threshold it is new.

Neither stage holds candidates for a person. A review queue with no review operation only drops news silently. If human review becomes a product requirement, add it as its own protected operation with an expiry.

An all-duplicate run completes with an explicit empty/no-new-opportunities result, not an assumed first invitation.

## Architectural changes versus the inspected source

- Move business orchestration out of `persistAndEmailTool` into application use cases and services; inject narrow dependencies at composition.
- Authorize the requested recipient/company/audience in the application boundary. An authenticated session alone is not permission to generate another recipient's brief.
- Validate candidates and await embeddings before accepting new stories, as requested. Check the exact source key first, resolve each candidate as its own retryable step, and use similarity as recorded evidence until a threshold is calibrated.
- Run every step as an execution identity acting for the recorded initiator and re-authorize on each business step.
- Use one shared model gateway port; keep module-specific prompts and schemas with the services that understand them.
- Use explicit run state, scope, durable dispatch, repeat-safe stage outputs, and atomic final publication.
- Separate optional email delivery from publishing the brief. Preserve `disableEmail` behavior rather than enabling delivery during a structural change.
- Handle zero new interviews explicitly. The inspected persistence tool indexes `createdInterviews[0]` even when every opportunity was skipped.

## Acceptance scenarios for a future implementation

1. Personal and target-customer variants retain their news categories and audience selection; delivery remains off when requested.
2. HTTP and agent entrypoints authorize identically and return the same run contract. Forged recipient/company/audience identifiers are denied.
3. A malformed generated candidate or failed embedding produces no new accepted story.
4. Same source, changed title: reuse the story without an embedding call. Similar title, distinct event: do not link solely on similarity. In observe mode a similar candidate is accepted and its nearest match recorded.
5. Two simultaneous attempts at the same source/opportunity produce one canonical record/link; duplicate workflow delivery does not create a second run.
6. A new recipient can receive an opportunity for an existing story; a repeated recipient/audience/story cannot create a second invitation.
7. A restart after embeddings or after publication reuses application stage results and does not republish completed work.
8. Zero results and all duplicates have explicit outcomes and do not assume an invitation exists. Every candidate has a terminal disposition.
9. Email failure remains visible and retryable without rolling back the published brief.
10. One candidate's embedding failure retries that candidate only; the search and other candidates are not repeated.
11. Access revoked after start stops the run at its next business step with an `accessRevoked` outcome and no publication.

These are acceptance criteria, not executed tests. This capture adds documentation and a visualization only.
