<!-- ai-generated: 80% - Codex drafted the explanation from the measured client and server percentiles -->

# Client-server latency gap

The measurement used a downstream Toxiproxy latency toxic of 100 ms with 10 ms jitter and toxicity 1.0. The
published `itsmlab load 3` profile ran for 60 seconds at 40 requests per second through
`http://host.docker.internal:8666`. The client-side latency-corrected p99 was 0.2792 s, while the p99 calculated
from the increments of the server histogram was 0.1750 s. Their measured difference was therefore 0.1042 s.

The gap is expected because the server histogram wraps request processing inside `svcdesk`, including the call to
`kb-index`, but it finishes observing before the response crosses the downstream proxy. Toxiproxy delays bytes on
the path back to the load generator, so that delay appears in the end-to-end client measurement and not in the
server's request-duration histogram. The result is close to the configured 100 ms latency; the additional few
milliseconds and run-to-run variation come from the 10 ms jitter, scheduling, network traversal, and percentile
sampling. This also demonstrates why a server RED histogram and an external latency SLI answer different but
complementary questions.
